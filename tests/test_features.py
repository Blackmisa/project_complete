"""Testes de feature engineering."""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from src.features.feature_engineering import (
    TicketSchema,
    build_features,
    clean_text,
)


def test_clean_text_lowercase() -> None:
    assert clean_text("PEDIDO ATRASADO") == "pedido atrasado"


def test_clean_text_removes_stopwords() -> None:
    result = clean_text("isso é o meu pedido aqui")
    assert "isso" not in result.split()
    assert "meu" not in result.split()
    assert "o" not in result.split()


def test_clean_text_keeps_meaningful_words() -> None:
    result = clean_text("pedido atrasado produto defeituoso reembolso")
    assert "pedido" in result
    assert "produto" in result
    assert "reembolso" in result


def test_clean_text_removes_email() -> None:
    result = clean_text("meu email é joao@example.com favor responder")
    assert "@" not in result


def test_clean_text_removes_cpf() -> None:
    result = clean_text("meu CPF é 123.456.789-09 favor verificar")
    assert "123" not in result


def test_clean_text_empty_string() -> None:
    assert clean_text("") == ""


def test_clean_text_none_returns_empty() -> None:
    assert clean_text(None) == ""  # type: ignore[arg-type]


def test_build_features_adds_column(sample_tickets: pd.DataFrame) -> None:
    result = build_features(sample_tickets)
    assert "cleaned_text" in result.columns


def test_build_features_preserves_count(sample_tickets: pd.DataFrame) -> None:
    result = build_features(sample_tickets)
    assert len(result) == len(sample_tickets)


def test_build_features_no_nulls(sample_tickets: pd.DataFrame) -> None:
    result = build_features(sample_tickets)
    assert result["cleaned_text"].notna().all()


def test_build_features_does_not_mutate_input(sample_tickets: pd.DataFrame) -> None:
    original_cols = list(sample_tickets.columns)
    build_features(sample_tickets)
    assert list(sample_tickets.columns) == original_cols


def test_ticket_schema_valid(sample_tickets: pd.DataFrame) -> None:
    TicketSchema.validate(sample_tickets[["message", "category"]])


def test_ticket_schema_rejects_null_message() -> None:
    bad_df = pd.DataFrame({"message": [None], "category": ["reembolso"]})
    with pytest.raises(pa.errors.SchemaError):
        TicketSchema.validate(bad_df)
