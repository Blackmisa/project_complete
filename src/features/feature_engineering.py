"""Feature engineering para classificação de tickets de atendimento."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

STOPWORDS_PT: set[str] = {
    "a", "ao", "aos", "as", "até", "com", "como", "da", "das", "de", "dela",
    "delas", "dele", "deles", "depois", "do", "dos", "e", "ela", "elas", "ele",
    "eles", "em", "entre", "era", "eram", "essa", "essas", "esse", "esses",
    "esta", "estas", "este", "estes", "eu", "foi", "foram", "há", "isso",
    "isto", "já", "lhe", "lhes", "mais", "mas", "me", "mesmo", "meu", "meus",
    "minha", "minhas", "muito", "na", "nas", "nem", "no", "nos", "nossa",
    "nossas", "nosso", "nossos", "num", "numa", "o", "os", "ou", "para",
    "pela", "pelas", "pelo", "pelos", "por", "qual", "quando", "que", "quem",
    "se", "seja", "sem", "seu", "seus", "sua", "suas", "também", "te", "tem",
    "têm", "teu", "teus", "tua", "tuas", "um", "uma", "umas", "uns", "você",
    "vocês",
}

_RE_URL = re.compile(r"https?://\S+")
_RE_EMAIL = re.compile(r"\S+@\S+\.\S+")
_RE_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
_RE_PHONE = re.compile(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}")
_RE_NON_ALPHA = re.compile(r"[^a-záéíóúâêîôûãõàèìòùç\d\s]")
_RE_SPACES = re.compile(r"\s+")


class TicketSchema(pa.DataFrameModel):
    message: Series[str] = pa.Field(nullable=False)
    category: Series[str] = pa.Field(nullable=False)

    class Config:
        coerce = True


def clean_text(text: str) -> str:
    """Normaliza texto: lowercase, remove PII, pontuação e stopwords."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFKC", text)
    text = _RE_URL.sub(" ", text)
    text = _RE_EMAIL.sub(" ", text)
    text = _RE_CPF.sub(" ", text)
    text = _RE_PHONE.sub(" ", text)
    text = _RE_NON_ALPHA.sub(" ", text)
    tokens = _RE_SPACES.sub(" ", text).strip().split()
    tokens = [t for t in tokens if t not in STOPWORDS_PT and len(t) > 1]
    return " ".join(tokens)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna cleaned_text ao dataframe."""
    df = df.copy()
    df["cleaned_text"] = df["message"].apply(clean_text)
    return df
