"""LLM-as-judge: avalia respostas do agente em 3 criterios de negocio."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import mlflow
from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent.rag_pipeline import retrieve

load_dotenv()
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden_set" / "golden.json"
REPORT_PATH = ROOT / "data" / "processed" / "llm_judge_report.json"

_JUDGE_PROMPT = """\
Avalie a resposta do assistente em relacao a pergunta e ao contexto.
Retorne APENAS um JSON com as chaves abaixo, valores entre 0.0 e 1.0:
- faithfulness: a resposta esta factualmente alinhada com os documentos?
- helpfulness: a resposta e util e responde adequadamente ao cliente?
- business_resolution: o problema foi resolvido sem necessidade de humano?

Pergunta: {question}
Contexto: {context}
Resposta: {answer}"""


def _generate_answer(question: str, context: str, client: Anthropic) -> str:
    msg = client.messages.create(
        model=os.getenv("LLM_MODEL", "claude-haiku-4-5"),
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Responda em portugues com base no contexto:\n\n{context}\n\nPergunta: {question}",
        }],
    )
    return msg.content[0].text


def _judge(question: str, context: str, answer: str, client: Anthropic) -> dict[str, float]:
    prompt = _JUDGE_PROMPT.format(question=question, context=context, answer=answer)
    msg = client.messages.create(
        model=os.getenv("LLM_MODEL", "claude-haiku-4-5"),
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        text = match.group()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Judge retornou JSON invalido: %s", text[:100])
        return {"faithfulness": 0.0, "helpfulness": 0.0, "business_resolution": 0.0}


def run_llm_judge(n_samples: int | None = None) -> dict[str, float]:
    """Roda LLM-as-judge e retorna metricas agregadas."""
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        golden = json.load(f)
    if n_samples:
        golden = golden[:n_samples]

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    all_scores: list[dict] = []

    for item in golden:
        docs = retrieve(item["query"], top_k=3)
        context = "\n\n".join(d["content"] for d in docs)
        answer = _generate_answer(item["query"], context, client)
        scores = _judge(item["query"], context, answer, client)
        all_scores.append(scores)
        logger.info("Julgado: %s", item["query"][:60])

    n = len(all_scores)
    aggregated: dict[str, float] = {
        "faithfulness": round(sum(s.get("faithfulness", 0.0) for s in all_scores) / n, 4),
        "helpfulness": round(sum(s.get("helpfulness", 0.0) for s in all_scores) / n, 4),
        "business_resolution": round(sum(s.get("business_resolution", 0.0) for s in all_scores) / n, 4),
        "n_samples": float(n),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)
    logger.info("LLM judge report salvo em %s", REPORT_PATH)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "datathon-fase05"))
    with mlflow.start_run(run_name="llm_judge"):
        mlflow.set_tag("eval_type", "llm_judge")
        mlflow.log_metrics({k: v for k, v in aggregated.items() if k != "n_samples"})
        mlflow.log_param("n_samples", int(aggregated["n_samples"]))
        mlflow.log_artifact(str(REPORT_PATH))

    return aggregated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    scores = run_llm_judge(n_samples=5)
    for k, v in scores.items():
        print(f"{k}: {v}")
