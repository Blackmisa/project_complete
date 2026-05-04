# Model Card — Classificador de Categoria de Ticket

> Template baseado em Mitchell et al. (2019) — _Model Cards for Model Reporting_.

## Identificação

- **Nome do modelo**: `ticket-category-classifier`
- **Versão**: 0.1.0
- **Tipo**: Classificação multiclasse (texto)
- **Owner**: Datathon Team — AmazoniaShop
- **Risk level**: `low` (decisão não é financeira nem afeta indivíduos diretamente)
- **Última atualização**: 2026-05-03
- **Git SHA**: N/A (repositório local sem remote configurado)

## Uso pretendido

- **Caso de uso primário**: roteamento automático de tickets de atendimento ao
  cliente para a categoria correta, otimizando tempo de resposta.
- **Usuários**: time de operações da AmazoniaShop (cenário fictício do Datathon).
- **Casos fora do escopo**: NÃO usar para decisões de crédito, score de cliente,
  detecção de fraude ou qualquer caso com impacto financeiro direto.

## Dados de treinamento

- **Origem**: dados sintéticos gerados via `src/data/generate_synthetic.py` com
  `Faker(pt_BR)`, seed=42.
- **Volume**: 500 tickets (400 treino / 100 teste, split estratificado 80/20).
- **Distribuição de classes** (holdout, 100 amostras):

| Categoria | Suporte (teste) | % aprox. |
|---|---|---|
| cancelamento | 11 | 11% |
| duvida_produto | 14 | 14% |
| elogio | 12 | 12% |
| pagamento_falhou | 13 | 13% |
| pedido_nao_chegou | 9 | 9% |
| produto_defeito | 12 | 12% |
| reembolso | 14 | 14% |
| troca | 15 | 15% |

- **Limitações**: dados sintéticos não capturam ambiguidade nem ruído de mensagens
  reais. Modelo final deve ser retreinado em dados reais antes de produção.

## Métricas

| Métrica | Valor (holdout) | Threshold mínimo |
|---|---|---|
| Acurácia | **1.00** | 0.70 |
| F1 (macro) | **1.00** | 0.65 |
| AUC (one-vs-rest) | **1.00** | — |

> **Nota**: scores perfeitos refletem a natureza sintética dos dados (Faker gera
> padrões altamente regulares). Espera-se queda significativa em dados reais.
> O modelo serve como baseline — não como solução final de produção.

## Análises de viés e fairness

- **Slices avaliados**: 8 categorias de ticket (ver distribuição acima).
- **Resultado**: classes equilibradas (min 9, max 15 amostras no holdout).
  `class_weight='balanced'` aplicado no treinamento por precaução.
- **Mitigações**: dados sintéticos foram gerados com distribuição uniforme entre
  categorias. Análise em dados reais (canais, horários, perfil demográfico)
  está no roadmap pós-Datathon.

## Decisões de design

- Escolha de TF-IDF + Logistic Regression em vez de modelo neural: dataset pequeno,
  baseline interpretável, treino em segundos, não requer GPU.
- Classes desbalanceadas tratadas via `class_weight='balanced'`.
- `max_features=5000`, `ngram_range=(1, 2)`, `solver='lbfgs'`.

## Limitações conhecidas

- Modelo treinado apenas em português brasileiro.
- Não foi avaliado em mensagens com gírias regionais ou typos pesados.
- Sintético: o modelo PODE estar superestimando seu desempenho em produção real.
- AUC e F1 = 1.00 são indicadores de dados limpos, não de generalização real.

## Como reproduzir

```bash
make data           # Gera dados (seed=42)
make train          # Treina e loga no MLflow
mlflow ui           # http://localhost:5000
```

## Referências

- Mitchell, M. et al. (2019). _Model Cards for Model Reporting_. FAT*.
