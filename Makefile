.PHONY: help install infra-up infra-down infra-logs data train serve test lint format clean eval-ragas eval-judge eval-drift eval

help:
	@echo "Comandos disponíveis:"
	@echo "  install       Instala dependências (requer uv ou pip)"
	@echo "  infra-up      Sobe Qdrant + MLflow + Langfuse"
	@echo "  infra-down    Derruba a infraestrutura"
	@echo "  infra-logs    Tail dos logs"
	@echo "  data          Gera dados sintéticos (tickets + KB + golden set)"
	@echo "  train         Treina baseline e loga no MLflow"
	@echo "  serve         Sobe API FastAPI em http://localhost:8000"
	@echo "  test          Roda pytest com cobertura"
	@echo "  lint          ruff + mypy + bandit"
	@echo "  format        ruff format"
	@echo "  eval-ragas    Avaliação RAGAS (requer infra-up)"
	@echo "  eval-judge    LLM-as-judge (requer ANTHROPIC_API_KEY)"
	@echo "  eval-drift    Detecção de drift com Evidently"
	@echo "  eval          Roda todas as avaliações"
	@echo "  clean         Remove caches"

install:
	@if command -v uv >/dev/null 2>&1; then \
		echo ">> Instalando com uv"; \
		uv pip install -e ".[dev]"; \
	else \
		echo ">> uv não encontrado, usando pip"; \
		pip install -e ".[dev]"; \
	fi

infra-up:
	docker compose up -d
	@echo ""
	@echo ">> Serviços disponíveis:"
	@echo "   Qdrant:   http://localhost:6333/dashboard"
	@echo "   MLflow:   http://localhost:5000"
	@echo "   Langfuse: http://localhost:3000  (admin@datathon.local / datathon123)"

infra-down:
	docker compose down

infra-logs:
	docker compose logs -f

data:
	python -m src.data.generate_synthetic

train:
	python -m src.models.train

serve:
	uvicorn src.serving.app:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest --cov=src --cov-report=term-missing --cov-fail-under=60

lint:
	ruff check src tests evaluation
	mypy src --ignore-missing-imports
	bandit -r src -c pyproject.toml -ll

format:
	ruff format src tests evaluation
	ruff check --fix src tests evaluation

eval-ragas:
	python -m evaluation.ragas_eval

eval-judge:
	python -m evaluation.llm_judge

eval-drift:
	python -m src.monitoring.drift

eval: eval-drift eval-judge eval-ragas

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
