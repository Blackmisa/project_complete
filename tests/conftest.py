"""Fixtures compartilhados para a suíte de testes."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture
def sample_tickets() -> pd.DataFrame:
    """DataFrame mínimo de tickets para testes unitários (sem PII real)."""
    return pd.DataFrame(
        [
            {
                "ticket_id": "TKT-000001",
                "channel": "chat",
                "category": "pedido_nao_chegou",
                "priority": "alta",
                "status": "aberto",
                "message": "Meu pedido AMZ12345 não chegou em 10 dias.",
                "resolution_time_hours": None,
            },
            {
                "ticket_id": "TKT-000002",
                "channel": "email",
                "category": "duvida_produto",
                "priority": "baixa",
                "status": "resolvido",
                "message": "Esse produto tem garantia?",
                "resolution_time_hours": 1.5,
            },
            {
                "ticket_id": "TKT-000003",
                "channel": "telefone",
                "category": "reembolso",
                "priority": "critica",
                "status": "escalado",
                "message": "Quero meu dinheiro de volta agora.",
                "resolution_time_hours": None,
            },
        ]
    )


@pytest.fixture
def sample_kb() -> list[dict]:
    """Mini KB para testes de retrieval."""
    return [
        {
            "doc_id": "KB-TEST-001",
            "topic": "garantia",
            "title": "Garantia",
            "content": "Garantia de 90 dias para todos os produtos.",
        },
        {
            "doc_id": "KB-TEST-002",
            "topic": "frete",
            "title": "Frete grátis",
            "content": "Frete grátis para compras acima de R$ 199.",
        },
    ]


@pytest.fixture
def sample_golden_set(tmp_path: Path) -> Path:
    """Cria um golden set temporário em arquivo, retorna o caminho."""
    data = [
        {
            "query": "Qual a garantia?",
            "expected_answer": "90 dias",
            "expected_doc_ids": ["KB-TEST-001"],
        }
    ]
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path
