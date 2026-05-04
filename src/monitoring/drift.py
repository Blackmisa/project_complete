"""Evidently 0.7 drift detection: golden set (reference) vs simulated current batch."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import mlflow
import pandas as pd
from dotenv import load_dotenv
from evidently import Report
from evidently.presets import DataDriftPreset

load_dotenv()
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = ROOT / "data" / "golden_set" / "golden.json"
REPORT_HTML = ROOT / "data" / "processed" / "drift_report.html"
REPORT_JSON = ROOT / "data" / "processed" / "drift_metrics.json"


def _load_golden_df() -> pd.DataFrame:
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame([
        {"query": item["query"], "expected_answer": item["expected_answer"]}
        for item in data
    ])


def _simulate_current_batch(reference: pd.DataFrame, drift_fraction: float = 0.3) -> pd.DataFrame:
    """Maioria identica ao reference + fração de queries fora de distribuicao."""
    n = len(reference)
    n_drift = max(1, int(n * drift_fraction))
    out_of_dist = pd.DataFrame({
        "query": [f"topico completamente diferente numero {i}" for i in range(n_drift)],
        "expected_answer": [f"resposta generica {i}" for i in range(n_drift)],
    })
    stable = reference.sample(n=n - n_drift, replace=True).reset_index(drop=True)
    return pd.concat([stable, out_of_dist], ignore_index=True)


def _extract_drift_scores(snapshot_dict: dict) -> dict[str, float]:
    """Extrai share e count de colunas com drift do dump_dict do snapshot."""
    share = 0.0
    count = 0.0
    for val in snapshot_dict.get("metric_results", {}).values():
        if isinstance(val, dict) and val.get("display_name") == "Count of Drifted Columns":
            share = float(val.get("share", {}).get("value", 0.0))
            count = float(val.get("count", {}).get("value", 0.0))
            break
    return {"share_of_drifted_columns": round(share, 4), "n_drifted_columns": int(count)}


def run_drift_detection(drift_fraction: float = 0.3) -> dict[str, float]:
    """Gera relatorio Evidently e loga metrica de drift no MLflow."""
    reference_df = _load_golden_df()
    current_df = _simulate_current_batch(reference_df, drift_fraction=drift_fraction)

    report = Report(metrics=[DataDriftPreset()])
    snapshot = report.run(current_data=current_df, reference_data=reference_df)

    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(REPORT_HTML))
    logger.info("Drift report HTML salvo em %s", REPORT_HTML)

    scores = _extract_drift_scores(snapshot.dump_dict())
    scores["n_columns"] = len(reference_df.columns)

    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "datathon-fase05"))
    with mlflow.start_run(run_name="drift_detection"):
        mlflow.set_tag("eval_type", "evidently_drift")
        mlflow.log_metric("share_of_drifted_columns", scores["share_of_drifted_columns"])
        mlflow.log_param("drift_fraction", drift_fraction)
        mlflow.log_artifact(str(REPORT_HTML))

    return scores


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    scores = run_drift_detection()
    for k, v in scores.items():
        print(f"{k}: {v}")
