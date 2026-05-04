"""Avaliação RAGAS do pipeline RAG contra o golden set."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import mlflow
from anthropic import Anthropic
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextPrecision, ContextRecall, Faithfulness, ResponseRelevancy

from src.agent.rag_pipeline import retrieve

load_dotenv()
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden_set" / "golden.json"
REPORT_PATH = ROOT / "data" / "processed" / "ragas_report.json"


def _generate_answer(query: str, contexts: list[str]) -> str:
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    context_text = "\n\n".join(contexts[:4])
    msg = client.messages.create(
        model=os.getenv("LLM_MODEL", "claude-haiku-4-5"),
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Com base nos documentos abaixo, responda a pergunta em portugues.\n\n"
                f"Documentos:\n{context_text}\n\nPergunta: {query}\n\nResposta:"
            ),
        }],
    )
    return msg.content[0].text


def run_ragas_eval(n_samples: int | None = None) -> dict[str, float]:
    """Roda avaliacao RAGAS e retorna metricas. Loga no MLflow."""
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        golden = json.load(f)
    if n_samples:
        golden = golden[:n_samples]

    llm = LangchainLLMWrapper(
        ChatAnthropic(
            model=os.getenv("LLM_MODEL", "claude-haiku-4-5"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    )
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name=os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
        )
    )

    samples = []
    for item in golden:
        docs = retrieve(item["query"], top_k=4)
        contexts = [d["content"] for d in docs]
        answer = _generate_answer(item["query"], contexts)
        samples.append(
            SingleTurnSample(
                user_input=item["query"],
                retrieved_contexts=contexts,
                response=answer,
                reference=item["expected_answer"],
            )
        )
        logger.info("Avaliado: %s", item["query"][:60])

    dataset = EvaluationDataset(samples=samples)
    metrics = [
        Faithfulness(llm=llm),
        ResponseRelevancy(llm=llm, embeddings=embeddings),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]

    result = evaluate(dataset=dataset, metrics=metrics)

    import math

    def _avg(val: object) -> float | None:
        if isinstance(val, list):
            valid = [v for v in val if v is not None and not (isinstance(v, float) and math.isnan(v))]
            return round(sum(valid) / len(valid), 4) if valid else None
        f = float(val)  # type: ignore[arg-type]
        return None if math.isnan(f) else round(f, 4)

    scores: dict[str, object] = {
        "faithfulness": _avg(result["faithfulness"]),
        "answer_relevancy": _avg(result["answer_relevancy"]),
        "context_precision": _avg(result["context_precision"]),
        "context_recall": _avg(result["context_recall"]),
        "n_samples": len(samples),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    logger.info("RAGAS report salvo em %s", REPORT_PATH)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "datathon-fase05"))
    with mlflow.start_run(run_name="ragas_eval"):
        mlflow.set_tag("eval_type", "ragas")
        mlflow.log_metrics({k: float(v) for k, v in scores.items() if k != "n_samples" and v is not None})
        mlflow.log_param("n_samples", scores["n_samples"])
        mlflow.log_artifact(str(REPORT_PATH))

    return scores


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    scores = run_ragas_eval(n_samples=None)
    for k, v in scores.items():
        print(f"{k}: {v}")
