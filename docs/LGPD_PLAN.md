# Plano de Conformidade LGPD — Assistente AmazoniaShop

> Aplicação prática da Lei nº 13.709/2018 (LGPD) ao sistema do Datathon.

## 1. Categorização de dados pessoais tratados

| Categoria | Exemplo nos tickets | Sensível? | Base legal (Art. 7º/9º) |
|---|---|---|---|
| Identificação | nome, email, CPF | Pessoal | Art. 7º, V (execução de contrato) |
| Contato | telefone, endereço | Pessoal | Art. 7º, V |
| Dado financeiro | valor de pedido | Pessoal | Art. 7º, V |
| Dado comportamental | histórico de tickets | Pessoal | Art. 7º, IX (interesse legítimo) |

**Não tratamos dados sensíveis** (Art. 5º, II) como saúde, biometria, dados raciais.

## 2. Princípios aplicados (Art. 6º)

- **Finalidade**: dados usados apenas para resolver o ticket do próprio cliente.
- **Adequação e necessidade**: PII removida do output do LLM via Presidio.
- **Livre acesso**: cliente pode solicitar seus dados via tool dedicada (roadmap)
  ou email `dpo@amazoniashop.com.br` (fictício).
- **Qualidade**: dados validados via `pandera` schemas.
- **Transparência**: System Card e este documento publicados no repositório.
- **Segurança**: dados em trânsito (TLS) e em repouso (criptografia do volume Docker em prod).
- **Não discriminação**: ver auditoria de viés no Model Card.
- **Responsabilização**: tracing completo no Langfuse com retenção de 90 dias.

## 3. Direitos dos titulares (Art. 18) — como atendemos

| Direito | Como o cliente exerce |
|---|---|
| Confirmação e acesso | Email para DPO + tool `get_my_data` (roadmap) |
| Correção | Painel "Minha Conta" no e-commerce |
| Anonimização / bloqueio / eliminação | Email para DPO; resposta em até 15 dias úteis |
| Portabilidade | Export JSON via "Minha Conta" (roadmap) |
| Eliminação após consentimento | Hard-delete em até 15 dias da solicitação |
| Informação sobre compartilhamento | Listado em `docs/PRIVACY.md` (roadmap) |
| Revogação de consentimento | Toggle em "Minha Conta" |

## 4. Tratamento específico no fluxo do agente

```
Input do cliente (pode conter PII)
        ↓
InputGuardrail (não loga PII em texto puro)
        ↓
Agente ReAct (contexto efêmero, descartado após resposta)
        ↓
OutputGuardrail (Presidio remove PII antes de devolver)
        ↓
Resposta ao cliente (sem PII vazada)
        ↓
Log no Langfuse (versão sanitizada)
```

**Justificativa**: o LLM é tratado como **operador** dos dados, não controlador.
A AmazoniaShop é a controladora. Dados não são usados para treinamento do LLM
(API com `data_retention_opt_out` habilitado).

## 5. Retenção e eliminação

| Tipo de dado | Tempo de retenção | Justificativa |
|---|---|---|
| Ticket original | 5 anos | Obrigação legal (Código Civil Art. 206) |
| Trace do agente (Langfuse) | 90 dias | Auditoria operacional |
| Logs de aplicação | 30 dias | Debugging e segurança |
| Backups | 12 meses | Continuidade de negócio |

Após cada período, hard-delete + auditoria registrada.

## 6. Incidentes (Art. 48)

Em caso de vazamento, prazo de **comunicação à ANPD em até 2 dias úteis**.
Plano de resposta documentado em `docs/INCIDENT_RESPONSE.md` (roadmap).

## 7. Encarregado (DPO)

- **Email**: `dpo@amazoniashop.com.br` (fictício para o Datathon)
- **Responsabilidades**: ponto único de contato com ANPD e titulares; revisão
  trimestral deste plano.

## 8. Pendências pós-Datathon

- [ ] Tool `get_my_data` no agente para auto-atendimento de direitos
- [ ] Registro de operações de tratamento (ROPA) formal
- [ ] DPIA (Data Protection Impact Assessment) para o agente automatizado
- [ ] Treinamento LGPD para o time de operações
