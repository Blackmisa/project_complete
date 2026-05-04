# System Card — Assistente de Atendimento AmazoniaShop

> Documenta o sistema integrado (agente + RAG + tools + guardrails).

## Visão geral

Sistema de atendimento automatizado para a AmazoniaShop (e-commerce fictício),
combinando:

- **Classificador ML** de categoria/prioridade de ticket (baseline TF-IDF + LR)
- **Agente ReAct** com 4 tools: `search_kb`, `get_order_status`,
  `classify_priority`, `escalate_to_human`
- **RAG** sobre base de conhecimento (30 documentos de FAQ/políticas)
- **Guardrails** de input (anti prompt-injection) e output (PII regex)

## Arquitetura

```
Cliente → API FastAPI → InputGuardrail → Agente ReAct
                                            ├── Tool: search_kb (RAG/Qdrant)
                                            ├── Tool: get_order_status (mock)
                                            ├── Tool: classify_priority (ML model)
                                            └── Tool: escalate_to_human
                                          ↓
                                      OutputGuardrail (regex PII)
                                          ↓
                                      Resposta ao cliente
                                          ↓
                              Langfuse (tracing) + Prometheus (métricas)
```

## Decisões de produto e ética

| Decisão | Justificativa |
|---|---|
| LLM via API gerenciada | Tradeoff: custo por chamada vs. risco operacional de servir modelo grande localmente em 2 dias. |
| PII removida do output | Compliance LGPD (Art. 18) e princípio da minimização. |
| Tool `escalate_to_human` sempre disponível | Princípio de _human-in-the-loop_ obrigatório em casos de baixa confiança ou tópicos sensíveis. |
| Telemetria habilitada por padrão | Auditabilidade exigida pela LGPD (Art. 37). |

## Métricas de qualidade

Avaliadas no golden set completo (`data/golden_set/golden.json`, 25 amostras) — 2026-05-03.

| Categoria | Métrica | Valor medido | Threshold | Status |
|---|---|---|---|---|
| RAG | faithfulness (RAGAS) | **0.8518** | ≥ 0.75 | ✅ |
| RAG | answer_relevancy | N/A¹ | ≥ 0.75 | — |
| RAG | context_precision | N/A¹ | ≥ 0.70 | — |
| RAG | context_recall | **0.88** | ≥ 0.70 | ✅ |
| Negócio | faithfulness (LLM-judge) | **0.92** | ≥ 0.75 | ✅ |
| Negócio | helpfulness (LLM-judge) | **0.73** | ≥ 0.60 | ✅ |
| Negócio | resolução sem humano | **0.58** | ≥ 0.60 | ⚠️ abaixo |
| Observabilidade | drift (share colunas) | **0.00** | ≤ 0.20 | ✅ |
| Operação | latência p95 | ~2–3s | ≤ 3s | ✅ estimado |

> ¹ `answer_relevancy` e `context_precision` retornaram NaN — algumas amostras
> não produziram embedding válido para cálculo de similaridade coseno.
> Os dois critérios com medição válida (faithfulness 0.85, context_recall 0.88)
> estão acima do threshold. O LLM-judge confirma qualidade: faithfulness 0.92.

## Riscos identificados e mitigações

Ver `OWASP_MAPPING.md` para o mapeamento completo OWASP Top 10 LLM.

| Risco | Severidade | Mitigação |
|---|---|---|
| Prompt injection | Alta | Regex no `InputGuardrail` + bloqueio de 8 padrões PT/EN |
| Vazamento de PII no output | Alta | `OutputGuardrail` — regex anonimiza CPF, e-mail, telefone |
| Resposta incorreta (alucinação) | Média | RAG ancora respostas + escalate_to_human disponível |
| Excessive agency do agente | Média | `max_iterations` do LangGraph + tools sem efeitos colaterais reais |
| Custo descontrolado | Média | Limite de 2000 chars no input + token budget no LLM |

## Modo de falha esperado

- **Pergunta fora do escopo da KB**: agente deve usar `escalate_to_human` em vez
  de inventar resposta.
- **Input com PII pesada**: guardrail deixa passar o texto, mas o output sanitiza.
- **LLM indisponível**: API retorna `500` com mensagem clara.

## Conformidade

- **LGPD**: ver `LGPD_PLAN.md`. Bases legais aplicadas: Art. 7º, II (cumprimento
  de obrigação contratual) e VII (proteção do crédito).
- **Direitos dos titulares**: implementados via tool dedicada futura (roadmap).

## Observabilidade

- **Tracing**: Langfuse coleta cada chamada do agente (input, output, tools usadas, tokens).
- **Métricas**: Prometheus expõe latência, taxa de erro, throughput em `/metrics`.
- **Drift**: Evidently roda comparando distribuição de inputs em produção vs. golden set.
  Report HTML em `data/processed/drift_report.html`.

## Roadmap pós-Datathon

1. Servir LLM local (vLLM + quantização AWQ) para reduzir custo e latência
2. Champion-challenger no classificador de categoria com dados reais
3. Retraining automatizado disparado por drift (PSI > 0.2)
4. Substituir tools mockadas (`get_order_status`) por integrações reais
5. Avaliação de fairness por slices demográficos
6. Aumentar golden set para ≥ 50 amostras para RAGAS mais estável
