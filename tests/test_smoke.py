"""Testes mínimos de sanidade — garantem que o pytest está funcional desde o setup.

Estes testes são substituídos por testes reais nos próximos sprints, mas servem
para validar que a infraestrutura de testes (pytest + coverage + CI) funciona.
"""

from __future__ import annotations

from pathlib import Path


def test_project_structure(project_root: Path) -> None:
    """Estrutura mínima de pastas existe."""
    expected_dirs = [
        "src",
        "tests",
        "evaluation",
        "docs",
        "configs",
        "data",
    ]
    for d in expected_dirs:
        assert (project_root / d).is_dir(), f"Pasta esperada ausente: {d}"


def test_pyproject_exists(project_root: Path) -> None:
    """pyproject.toml está presente — exigência da rubrica (Fase 01)."""
    assert (project_root / "pyproject.toml").is_file()


def test_sample_tickets_fixture(sample_tickets) -> None:
    """Fixture de tickets carrega corretamente e tem as colunas mínimas."""
    required_cols = {"ticket_id", "category", "priority", "status", "message"}
    assert required_cols.issubset(set(sample_tickets.columns))
    assert len(sample_tickets) > 0


def test_sample_kb_fixture(sample_kb) -> None:
    """Fixture de KB tem schema esperado."""
    assert len(sample_kb) > 0
    for doc in sample_kb:
        assert {"doc_id", "title", "content"}.issubset(set(doc.keys()))
