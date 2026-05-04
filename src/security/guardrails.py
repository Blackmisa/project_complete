"""Guardrails de entrada e saída para o endpoint /chat."""

from __future__ import annotations

import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Input guardrail — prompt injection & abuse detection
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[str] = [
    r"\bignore\b.{0,30}\binstru[çc][õo]es?\b",
    r"(you\s+are\s+now|agora\s+voc[êe]\s+[eé])\s+",
    r"(act\s+as|atue\s+como|finja\s+ser|pretend\s+to\s+be)\s+",
    r"(nova\s+persona|new\s+persona|novo\s+papel)",
    r"(system\s*prompt|prompt\s+interno)",
    r"(jailbreak|dan\s+mode|modo\s+irrestrito|sem\s+filtros?)",
    r"(reveal|revelar|mostrar)\s+.{0,40}(prompt|instru[çc][õo]es?)",
    r"(esqueça?|forget)\s+.{0,40}(instru[çc][õo]es?|regras?)",
]

_MAX_INPUT_LENGTH = 2_000


class InputGuardrail:
    """Valida mensagens de entrada: rejeita injection e inputs excessivamente longos."""

    _compiled: ClassVar[list[re.Pattern[str]]] = [
        re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS
    ]

    def check(self, text: str) -> str:
        """Retorna o texto se for seguro; levanta ValueError caso contrário."""
        if len(text) > _MAX_INPUT_LENGTH:
            raise ValueError(
                f"Mensagem excede {_MAX_INPUT_LENGTH} caracteres. "
                "Por favor, seja mais conciso."
            )
        for pattern in self._compiled:
            if pattern.search(text):
                logger.warning("Tentativa de prompt injection bloqueada: %.80s", text)
                raise ValueError(
                    "Sua mensagem contém conteúdo não permitido. "
                    "Por favor, reformule sua dúvida sobre os serviços da AmazoniaShop."
                )
        return text


# ---------------------------------------------------------------------------
# Output guardrail — PII anonymization
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[str, str]] = [
    # CPF — formatos: 123.456.789-00 ou 12345678900
    (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "<CPF_REDACTED>"),
    # E-mail
    (r"[\w.+\-]+@[\w\-]+\.[\w.\-]+", "<EMAIL_REDACTED>"),
    # Telefone BR — (11) 91234-5678 / 11912345678 / +55 11 91234-5678
    (r"\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}|\d{4})-?\d{4}\b", "<PHONE_REDACTED>"),
]


class OutputGuardrail:
    """Anonimiza PII (CPF, e-mail, telefone) nas respostas do agente."""

    _compiled: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (re.compile(p, re.IGNORECASE), repl) for p, repl in _PII_PATTERNS
    ]

    def sanitize(self, text: str) -> str:
        """Substitui entidades PII por placeholders e retorna texto limpo."""
        for pattern, replacement in self._compiled:
            text = pattern.sub(replacement, text)
        return text
