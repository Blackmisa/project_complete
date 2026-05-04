"""Pipeline TF-IDF + LogisticRegression para classificação de tickets."""

from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def build_pipeline(config: dict[str, Any]) -> Pipeline:
    """Constrói pipeline sklearn a partir de config."""
    vec_cfg = config["vectorizer"]
    hp = config["hyperparams"]

    vectorizer = TfidfVectorizer(
        max_features=vec_cfg["max_features"],
        ngram_range=tuple(vec_cfg["ngram_range"]),
        min_df=vec_cfg["min_df"],
        sublinear_tf=True,
    )
    classifier = LogisticRegression(
        C=hp["C"],
        max_iter=hp["max_iter"],
        class_weight=hp["class_weight"],
        random_state=42,
        solver="lbfgs",
    )
    return Pipeline([("tfidf", vectorizer), ("lr", classifier)])
