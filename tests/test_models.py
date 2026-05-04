"""Testes do modelo baseline."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.feature_engineering import build_features
from src.models.baseline import build_pipeline

_MOCK_CONFIG = {
    "vectorizer": {"max_features": 200, "ngram_range": [1, 2], "min_df": 1},
    "hyperparams": {"C": 1.0, "max_iter": 200, "class_weight": "balanced"},
}


@pytest.fixture
def small_dataset() -> pd.DataFrame:
    messages = [
        "meu pedido não chegou ainda prazo expirou",
        "quero cancelar minha compra hoje",
        "produto chegou com defeito quebrado",
        "quero reembolso do valor pago cartão",
        "dúvida sobre produto disponibilidade estoque",
        "pedido atrasado sem previsão entrega",
        "cancelar pedido urgente arrependimento",
        "produto com defeito na embalagem amassada",
        "quando chega meu pedido rastrear",
        "reembolso não foi creditado conta",
        "pagamento recusado cartão falhou transação",
        "não consigo pagar boleto vencido",
    ]
    categories = [
        "pedido_nao_chegou", "cancelamento", "produto_defeito",
        "reembolso", "duvida_produto", "pedido_nao_chegou",
        "cancelamento", "produto_defeito", "pedido_nao_chegou",
        "reembolso", "pagamento_falhou", "pagamento_falhou",
    ]
    df = pd.DataFrame({"message": messages, "category": categories})
    return build_features(df)


def test_pipeline_builds() -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    assert pipeline is not None
    assert hasattr(pipeline, "fit")
    assert hasattr(pipeline, "predict")


def test_pipeline_fits_and_predicts(small_dataset: pd.DataFrame) -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    X = small_dataset["cleaned_text"]
    y = small_dataset["category"]
    pipeline.fit(X, y)
    preds = pipeline.predict(X)
    assert len(preds) == len(X)


def test_predict_valid_classes(small_dataset: pd.DataFrame) -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    X = small_dataset["cleaned_text"]
    y = small_dataset["category"]
    pipeline.fit(X, y)
    preds = pipeline.predict(X)
    assert set(preds).issubset(set(y))


def test_predict_proba_sums_to_one(small_dataset: pd.DataFrame) -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    X = small_dataset["cleaned_text"]
    y = small_dataset["category"]
    pipeline.fit(X, y)
    proba = pipeline.predict_proba(X)
    assert proba.shape[0] == len(X)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-5)


def test_predict_proba_n_classes(small_dataset: pd.DataFrame) -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    X = small_dataset["cleaned_text"]
    y = small_dataset["category"]
    pipeline.fit(X, y)
    proba = pipeline.predict_proba(X)
    assert proba.shape[1] == len(y.unique())


def test_pipeline_named_steps() -> None:
    pipeline = build_pipeline(_MOCK_CONFIG)
    assert "tfidf" in pipeline.named_steps
    assert "lr" in pipeline.named_steps
