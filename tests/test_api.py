"""Testes da API FastAPI — endpoints /chat, /health, /metrics."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_MOCK_RESULT = {
    "answer": "Seu pedido esta em transito e chegara em 3 dias uteis.",
    "used_tools": ["search_kb", "get_order_status"],
    "trace_id": "test-session-001",
}


@pytest.fixture(scope="module")
def client():
    with (
        patch("src.serving.app.index_knowledge_base", return_value=30),
        patch("src.serving.app.run_agent", return_value=_MOCK_RESULT) as mock_agent,
    ):
        from src.serving.app import app

        with TestClient(app) as c:
            yield c, mock_agent


def test_health(client: tuple) -> None:
    c, _ = client
    resp = c.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_happy_path(client: tuple) -> None:
    c, _ = client
    resp = c.post(
        "/chat",
        json={"message": "Onde esta meu pedido AMZ12345?", "session_id": "sess-1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == _MOCK_RESULT["answer"]
    assert body["trace_id"] == "sess-1"
    assert isinstance(body["used_tools"], list)


def test_chat_generates_session_id_when_missing(client: tuple) -> None:
    c, _ = client
    resp = c.post("/chat", json={"message": "Ola"})
    assert resp.status_code == 200
    assert resp.json()["trace_id"] != ""


def test_chat_uses_provided_session_id(client: tuple) -> None:
    c, _ = client
    resp = c.post("/chat", json={"message": "Teste", "session_id": "minha-sessao"})
    assert resp.status_code == 200
    assert resp.json()["trace_id"] == "minha-sessao"


def test_chat_agent_error_returns_500(client: tuple) -> None:
    c, mock_agent = client
    mock_agent.side_effect = RuntimeError("falha simulada")
    resp = c.post("/chat", json={"message": "Erro proposital"})
    assert resp.status_code == 500
    mock_agent.side_effect = None
    mock_agent.return_value = _MOCK_RESULT


def test_metrics_endpoint(client: tuple) -> None:
    c, _ = client
    resp = c.get("/metrics")
    assert resp.status_code == 200
    assert b"chat_requests_total" in resp.content
    assert b"chat_latency_seconds" in resp.content
