# Datathon FIAP — Fase 05: Assistente de Atendimento AmazoniaShop

> **Pós-Tech MLET | Datathon | Fase 05 — LLMs e Agentes**
>
> Solução end-to-end de um assistente conversacional para a AmazoniaShop —
> e-commerce fictício de produtos regionais — combinando ML clássico, RAG,
> agente ReAct, observabilidade e governança.

## O problema (cenário fictício)

A AmazoniaShop processa milhares de tickets de atendimento por dia. Hoje, todos
caem em uma fila única, são lidos manualmente por agentes humanos, e o tempo
médio de resolução é alto. **Objetivo**: construir um sistema que automatize a
resolução de ~60% dos tickets de baixa complexidade e roteie os demais para a
fila correta com prioridade adequada, mantendo conformidade com LGPD.

### Métricas de negócio

| Métrica | Antes (baseline humano) | Meta com o sistema |
|---|---|---|
| % de tickets resolvidos sem humano | 0% | ≥ 60% |
| Tempo médio de primeira resposta | ~ 2h | ≤ 30s |
| Acurácia de roteamento por categoria | ~70% (manual) | ≥ 85% (modelo) |
| Custo por ticket atendido | R$ 4,50 (estimativa) | ≤ R$ 0,50 |

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│  Cliente → API FastAPI                                         │
│              ↓                                                  │
│        InputGuardrail (anti prompt injection)                  │
│              ↓                                                  │
│        Agente ReAct (LLM via Anthropic API)                    │
│              ├── Tool: search_kb       (RAG sobre Qdrant)      │
│              ├── Tool: get_order_status (mock interno)         │
│              ├── Tool: classify_priority (modelo TF-IDF + LR)  │
│              └── Tool: escalate_to_human                       │
│              ↓                                                  │
│        OutputGuardrail (Presidio remove PII)                   │
│              ↓                                                  │
│        Resposta ao cliente                                     │
│              ↓                                                  │
│  Langfuse (tracing) + MLflow (modelos) + Evidently (drift)     │
└─────────────────────────────────────────────────────────────────┘
```

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11 |
| ML clássico | scikit-learn, pandera, MLflow |
| LLM | Anthropic Claude (via API) |
| RAG | Qdrant + sentence-transformers (multilíngue) |
| Agente | LangChain ReAct |
| API | FastAPI + Uvicorn |
| Avaliação | RAGAS (4 métricas) + LLM-as-judge |
| Observabilidade | Langfuse + Prometheus + Evidently |
| Segurança | Microsoft Presidio + regex guardrails |
| Qualidade | ruff + mypy + bandit + pytest (≥60% cov) |
| CI/CD | GitHub Actions |

## Início rápido

### 1. Pré-requisitos

- Python 3.11
- Docker + Docker Compose
- (Opcional) `uv` para instalação mais rápida — `pip install uv`

### 2. Configuração

```bash
# Clone e entre no diretório
cd datathon-sprint0

# Crie ambiente virtual e instale dependências
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
# .venv\Scripts\activate      # Windows
make install

# Configure secrets (copie e preencha sua API key da Anthropic)
cp .env.example .env
# edite .env e coloque sua ANTHROPIC_API_KEY
```

### 3. Suba a infraestrutura

```bash
make infra-up
```

Serviços disponíveis:

- **Qdrant** dashboard: http://localhost:6333/dashboard
- **MLflow** UI: http://localhost:5000
- **Langfuse**: http://localhost:3000 (login: `admin@datathon.local` / `datathon123`)

### 4. Gere os dados sintéticos

```bash
make data
```

Gera:
- `data/raw/tickets.csv` — 500 tickets sintéticos com PII (Faker pt_BR)
- `data/raw/knowledge_base.json` — 30 documentos de FAQ (em português)
- `data/golden_set/golden.json` — 25 pares (query, resposta, contextos)

### 5. Rode os testes (sanidade do setup)

```bash
make test
```

Deve passar com cobertura ≥ 60%.

### 6. Próximos passos (você desenvolve aqui)

Veja `docs/ROADMAP_2_DIAS.md` para o cronograma detalhado.

## Roadmap das 4 etapas

- [x] **Sprint 0 — Setup**: infra, dados sintéticos, scaffolding
- [x] **Sprint 1 — Etapa 1**: EDA + baseline ML (F1=1.00) + MLflow + testes
- [x] **Sprint 2 — Etapa 2**: RAG no Qdrant + agente ReAct + FastAPI + CI completo
- [x] **Sprint 3 — Etapa 3**: RAGAS (faith=0.72) + LLM-judge (faith=0.92) + Langfuse + Evidently drift
- [x] **Sprint 4 — Etapa 4**: guardrails (input+output) + 6 cenários red team + System Card + Model Card

## Comandos comuns

```bash
make help          # Lista todos os atalhos
make infra-up      # Sobe Qdrant + MLflow + Langfuse
make data          # Gera dados sintéticos
make train         # Treina baseline (após Sprint 1)
make serve         # API em http://localhost:8000 (após Sprint 2)
make test          # pytest com cobertura
make lint          # ruff + mypy + bandit
make format        # auto-format do código
```

## Estrutura do repositório

```
.
├── .github/workflows/ci.yml       # GitHub Actions
├── configs/model_config.yaml      # Hiperparâmetros centralizados
├── data/
│   ├── raw/                       # Dados sintéticos gerados (não commitar)
│   └── golden_set/                # 25 pares para RAGAS
├── docs/
│   ├── MODEL_CARD.md              # Mitchell et al. (2019)
│   ├── SYSTEM_CARD.md             # Visão de sistema completo
│   ├── OWASP_MAPPING.md           # 6 ameaças OWASP LLM mapeadas
│   ├── LGPD_PLAN.md               # Plano de conformidade LGPD
│   └── RED_TEAM_REPORT.md         # 6 cenários adversariais
├── evaluation/                    # RAGAS + LLM-as-judge (Sprint 3)
├── notebooks/                     # EDA (Sprint 1)
├── src/
│   ├── agent/                     # ReAct + tools (Sprint 2)
│   ├── data/generate_synthetic.py # Geração de dados [pronto]
│   ├── features/                  # Feature engineering (Sprint 1)
│   ├── models/                    # Treino e inferência (Sprint 1)
│   ├── monitoring/                # Drift + métricas (Sprint 3)
│   ├── security/                  # Guardrails (Sprint 4)
│   └── serving/                   # FastAPI (Sprint 2)
├── tests/                         # pytest (≥ 60% cov)
├── docker-compose.yml             # Toda a infra local
├── Makefile                       # Atalhos
├── pyproject.toml                 # Deps + config das ferramentas
└── README.md
```

## Compliance e governança

- **LGPD**: ver `docs/LGPD_PLAN.md`
- **Model Card**: `docs/MODEL_CARD.md`
- **System Card**: `docs/SYSTEM_CARD.md`
- **Análise de risco (OWASP LLM)**: `docs/OWASP_MAPPING.md`
- **Red team**: `docs/RED_TEAM_REPORT.md`

## Limitações conhecidas (transparência)

Esta entrega foi desenvolvida em **2 dias por uma pessoa solo**. Decisões de
escopo intencionais, documentadas no System Card:

- LLM consumido via API gerenciada (não servido localmente com vLLM)
- DVC inicializado mas não conectado a remote storage
- Champion-challenger e retraining automatizado deixados como roadmap
- Red teaming com 6 cenários (vs. ferramenta automatizada como Garak)

A escolha foi **priorizar uma demonstração end-to-end coerente** em vez de
componentes isolados de alta sofisticação.

## Referências

- Yao et al. (2023) — _ReAct: Synergizing Reasoning and Acting in Language Models_
- Es et al. (2024) — _RAGAS: Automated Evaluation of Retrieval Augmented Generation_
- Mitchell et al. (2019) — _Model Cards for Model Reporting_
- OWASP (2025) — _Top 10 for LLM Applications_
- Brasil (2018) — _Lei nº 13.709/2018 (LGPD)_
