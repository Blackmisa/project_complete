# Roadmap — 48 horas de Datathon

> Cronograma operacional. Cada bloco tem entregáveis claros e critério de "pronto".
> Se um bloco estourar 1.5x o tempo, **corta escopo e segue**.

## Pré-voo (antes do dia 1)

- [ ] Conta Anthropic com créditos (US$ 5 já dão e sobram para o Datathon)
- [ ] Docker Desktop / Docker Engine rodando
- [ ] Python 3.11 instalado
- [ ] Repositório no GitHub criado

---

## Dia 1

### Manhã (4h) — Setup pronto, baseline rodando

**Bloco 1.1 (1h) — Setup**
- [x] Estrutura do repo (já feita pelo Sprint 0)
- [ ] `make install` funciona
- [ ] `make infra-up` sobe os 4 containers
- [ ] `.env` preenchido com `ANTHROPIC_API_KEY`
- [ ] `make data` gera os 3 artefatos
- [ ] `make test` passa
- [ ] Primeiro commit + push

**Bloco 1.2 (3h) — Etapa 1: EDA + Baseline + MLflow**
- [ ] `notebooks/01_eda.ipynb`: distribuição de classes, top palavras por categoria, comprimento médio de mensagem, % com PII detectada
- [ ] `src/features/feature_engineering.py`: limpeza de texto + lowercasing + remoção de stopwords pt
- [ ] `src/models/baseline.py`: TF-IDF + LogisticRegression (multiclasse)
- [ ] `src/models/train.py`: pipeline completo, `mlflow.log_*` com tags padronizadas (ver GAP 05 do guia)
- [ ] `tests/test_features.py`: schema com pandera, sem nulos, contagem preservada
- [ ] `tests/test_models.py`: modelo treina, predict tem shape correto, métricas dentro de range
- [ ] `make train` loga run no MLflow com AUC + F1 + precision + recall

**Critério de pronto Etapa 1**: MLflow UI mostra a run com métricas e o modelo registrado.

### Tarde (5h) — Etapa 2: RAG + Agente + API

**Bloco 1.3 (2h) — RAG**
- [ ] `src/agent/rag_pipeline.py`: chunk dos docs da KB → embed com sentence-transformers → upsert no Qdrant
- [ ] Função `retrieve(query, top_k=4)` retorna lista de chunks com score
- [ ] Teste manual: pergunta "como rastrear pedido?" deve trazer KB-002

**Bloco 1.4 (2h) — Agente ReAct + Tools**
- [ ] `src/agent/tools.py`: 4 tools com schemas Pydantic
  - `search_kb(query)` — chama o RAG
  - `get_order_status(order_id)` — mock que retorna status fake
  - `classify_priority(message)` — usa o modelo da Etapa 1
  - `escalate_to_human(reason)` — apenda em arquivo/log
- [ ] `src/agent/react_agent.py`: `create_react_agent` com Anthropic, prompt em pt-BR
- [ ] System prompt com instrução defensiva contra prompt injection

**Bloco 1.5 (1h) — FastAPI**
- [ ] `src/serving/app.py`: endpoint `POST /chat` recebe `{message, session_id}` e retorna `{answer, trace_id, used_tools}`
- [ ] Endpoint `GET /health` e `GET /metrics` (prometheus_client)
- [ ] `tests/test_api.py`: TestClient cobre happy path

**Critério de pronto Etapa 2**: `make serve` sobe a API, `curl POST /chat` retorna resposta sensata.

### Noite (3h) — Guardrails básicos + CI

**Bloco 1.6 (2h) — Guardrails**
- [ ] `src/security/guardrails.py`: classe `InputGuardrail` (regex de injection) e `OutputGuardrail` (Presidio)
- [ ] Plug guardrails no fluxo do `/chat`
- [ ] `tests/test_guardrails.py`: 6+ casos (injection bloqueada, PII anonimizada, input grande rejeitado, input limpo passa)

**Bloco 1.7 (1h) — CI verde + commit**
- [ ] Push e GitHub Actions verde (lint, format check, mypy, bandit, pytest com cov ≥ 60%)
- [ ] Tag `v0.1.0` (entrega da Etapa 1+2)

---

## Dia 2

### Manhã (4h) — Etapa 3: Avaliação + Observabilidade

**Bloco 2.1 (2h) — RAGAS + LLM-as-judge**
- [ ] `evaluation/ragas_eval.py`: roda contra `golden.json`, calcula 4 métricas, salva relatório em `data/processed/ragas_report.json`
- [ ] `evaluation/llm_judge.py`: 3 critérios — `faithfulness`, `helpfulness`, `business_resolution` (resolução sem humano)
- [ ] Loga métricas no MLflow no mesmo experimento

**Bloco 2.2 (1h) — Telemetria com Langfuse**
- [ ] Instrumenta o agente com `langfuse.observe`
- [ ] Cada request gera trace com input, output, tools usadas, tokens
- [ ] Dashboard nativo do Langfuse mostra latência p50/p95, custo por request

**Bloco 2.3 (1h) — Drift Detection**
- [ ] `src/monitoring/drift.py`: Evidently com `DataDriftPreset` comparando golden set (referência) vs. um lote simulado de inputs (atual)
- [ ] Salva HTML report em `data/processed/drift_report.html`
- [ ] Loga `share_of_drifted_columns` no MLflow

**Critério de pronto Etapa 3**: 4 RAGAS scores ≥ 0.7, Langfuse mostra traces, drift report HTML aberto.

### Tarde (4h) — Etapa 4: Segurança formal + Docs

**Bloco 2.4 (2h) — Red teaming**
- [ ] Roda os 6 cenários do `RED_TEAM_REPORT.md` manualmente
- [ ] Preenche resultados e marca status (✅/⚠️/❌)
- [ ] Para cenários ⚠️/❌: adiciona mitigação ou documenta como "limitação conhecida"

**Bloco 2.5 (2h) — Preencher docs**
- [ ] `MODEL_CARD.md`: preencher métricas reais, distribuição de classes, slices
- [ ] `SYSTEM_CARD.md`: preencher tabela de RAGAS, decisões finais
- [ ] `OWASP_MAPPING.md`: já está completo, só revisar
- [ ] `LGPD_PLAN.md`: já está completo, só revisar
- [ ] `README.md`: atualizar seção "Limitações conhecidas" com o que foi/não foi feito

**Critério de pronto Etapa 4**: 6 docs preenchidos, 6 cenários red team com resultado.

### Noite (3h) — Pitch + ensaio

**Bloco 2.6 (2h) — Slides do pitch**

Estrutura de 8 slides para 10 minutos:

1. **Capa** — Nome do projeto, sua identificação, foto/screenshot da arquitetura
2. **Problema** (1 min) — A AmazoniaShop tem fila única; tempo de resposta alto; custo alto. Métricas de baseline.
3. **Solução** (1 min) — Diagrama de arquitetura (cole o do README)
4. **Demo ao vivo** (3 min) — Abra a API e mostre 3 perguntas reais sendo respondidas. Mostre Langfuse com o trace.
5. **Métricas técnicas** (1.5 min) — RAGAS scores, latência p95, cobertura de testes
6. **Métricas de negócio** (1 min) — % de resolução sem humano, custo por ticket
7. **Segurança & Governança** (1 min) — OWASP mapping, red team, LGPD plan, Model/System Card
8. **Próximos passos & Q&A** (1.5 min) — Roadmap honesto: vLLM local, retraining, fairness

**Bloco 2.7 (1h) — Ensaio cronometrado**
- [ ] 1ª passada: cronometra, anota onde estoura. Provavelmente vai dar 12-13 min.
- [ ] Corta gordura, refina transições
- [ ] 2ª passada: deve ficar entre 9 e 10 min
- [ ] Backup: salva slides em PDF + screenshots da demo (caso a API caia)

---

## Dicas de sobrevivência

### Coisas que vão dar errado e como reagir

- **`pip install` demora muito**: use `uv pip install` se possível (10x mais rápido)
- **Modelo de embedding não baixa**: tem ~500MB; rode `make data` cedo para que o cache já esteja pronto
- **Anthropic API com erro 529 (overloaded)**: retry com backoff, ou tenha um arquivo `.env.openai` com `OPENAI_API_KEY` como fallback
- **Qdrant não conecta**: cheque `docker compose ps`, se necessário `docker compose restart qdrant`
- **Langfuse demora pra subir na primeira vez**: ~ 1 min para inicializar o banco. Espere e cheque http://localhost:3000
- **Coverage abaixo de 60%**: adicione testes triviais nos módulos sem cobertura (importação, tipos), não estresse
- **RAGAS muito lento**: rode em 5-10 amostras do golden set para iterar rápido; depois rode no set completo só na hora final
- **CI vermelho na hora final**: comente temporariamente o teste falhando, abre issue no GitHub mencionando, e segue. **Honestidade > nota perfeita.**

### Princípio guia

Se em qualquer momento você se pegar perdido em uma rabbit hole de >1h, pare,
respire, e pergunte: **"isso aparece na rubrica? quanto vale?"**. Se a resposta
for "não muito", documente como roadmap e siga em frente.

Boa sorte. 🚀
