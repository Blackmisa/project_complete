"""Script de treino: carrega dados, engenharia de features, treina baseline, loga no MLflow."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import joblib
import mlflow
import pandas as pd
import yaml
from dotenv import load_dotenv
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.features.feature_engineering import TicketSchema, build_features
from src.models.baseline import build_pipeline

load_dotenv()

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "model_config.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data(config: dict) -> pd.DataFrame:
    path = ROOT / config["data"]["raw_tickets"]
    df = pd.read_csv(path)
    return df


def train(config: dict | None = None) -> dict[str, float]:
    if config is None:
        config = load_config()

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "datathon-fase05")

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    df = load_data(config)
    TicketSchema.validate(df[["message", "category"]])
    df = build_features(df)

    bl_cfg = config["baseline"]
    X = df["cleaned_text"]
    y = df[bl_cfg["target"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=bl_cfg["test_size"],
        random_state=config["data"]["random_state"],
        stratify=y,
    )

    pipeline = build_pipeline(bl_cfg)

    with mlflow.start_run(run_name="baseline_tfidf_lr") as run:
        mlflow.set_tags(
            {
                "model_type": "tfidf_logistic_regression",
                "stage": "baseline",
                "sprint": "1",
            }
        )
        mlflow.log_params(
            {
                "max_features": bl_cfg["vectorizer"]["max_features"],
                "ngram_range": str(bl_cfg["vectorizer"]["ngram_range"]),
                "C": bl_cfg["hyperparams"]["C"],
                "max_iter": bl_cfg["hyperparams"]["max_iter"],
                "class_weight": bl_cfg["hyperparams"]["class_weight"],
                "test_size": bl_cfg["test_size"],
                "n_train": len(X_train),
                "n_test": len(X_test),
            }
        )

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)

        f1 = f1_score(y_test, y_pred, average="weighted")
        precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)

        try:
            auc = roc_auc_score(
                pd.get_dummies(y_test).reindex(columns=pipeline.classes_, fill_value=0).values,
                y_prob,
                average="macro",
                multi_class="ovr",
            )
        except Exception:
            auc = float("nan")

        mlflow.log_metrics(
            {
                "f1_weighted": round(f1, 4),
                "precision_weighted": round(precision, 4),
                "recall_weighted": round(recall, 4),
                "auc_macro": round(auc, 4) if auc == auc else 0.0,
            }
        )

        processed_dir = ROOT / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

        report_path = processed_dir / "classification_report.txt"
        report_path.write_text(
            classification_report(y_test, y_pred), encoding="utf-8"
        )
        mlflow.log_artifact(str(report_path))

        run_id = run.info.run_id

        model_path = processed_dir / "baseline_model.pkl"
        joblib.dump(pipeline, model_path)
        mlflow.log_artifact(str(model_path), artifact_path="model")

        logger.info("Run ID: %s", run_id)
        logger.info(
            "F1=%.4f | Precision=%.4f | Recall=%.4f | AUC=%.4f",
            f1,
            precision,
            recall,
            auc,
        )

    return {"f1": f1, "precision": precision, "recall": recall, "auc": auc}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    metrics = train()
    print(f"F1={metrics['f1']:.4f} | AUC={metrics['auc']:.4f}")
