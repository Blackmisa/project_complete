"""RAG pipeline: indexa a knowledge base no Qdrant e recupera chunks relevantes."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
KB_PATH = ROOT / "data" / "raw" / "knowledge_base.json"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "kb_atendimento")
VECTOR_DIM = 384

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Carregando modelo de embedding: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def index_knowledge_base(force: bool = False) -> int:
    """Carrega KB, gera embeddings e faz upsert no Qdrant. Retorna nº de docs indexados."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing and not force:
        count = client.count(COLLECTION_NAME).count
        if count > 0:
            logger.info("Colecao '%s' ja possui %d docs. Pulando indexacao.", COLLECTION_NAME, count)
            return count
        client.delete_collection(COLLECTION_NAME)

    if COLLECTION_NAME not in existing or force:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )

    with KB_PATH.open(encoding="utf-8") as f:
        docs = json.load(f)

    model = _get_model()
    texts = [f"{doc['title']}\n{doc['content']}" for doc in docs]
    embeddings = model.encode(texts, show_progress_bar=False)

    points = [
        PointStruct(
            id=i,
            vector=emb.tolist(),
            payload={
                "doc_id": doc["doc_id"],
                "topic": doc["topic"],
                "title": doc["title"],
                "content": doc["content"],
            },
        )
        for i, (doc, emb) in enumerate(zip(docs, embeddings))
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("Indexados %d documentos na colecao '%s'.", len(points), COLLECTION_NAME)
    return len(points)


def retrieve(query: str, top_k: int = 4, score_threshold: float = 0.3) -> list[dict[str, Any]]:
    """Recupera os chunks mais relevantes para a query."""
    client = _get_client()
    model = _get_model()

    query_vec = model.encode(query).tolist()
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        limit=top_k,
        score_threshold=score_threshold,
    )

    return [
        {
            "doc_id": r.payload["doc_id"],
            "title": r.payload["title"],
            "content": r.payload["content"],
            "score": round(r.score, 4),
        }
        for r in response.points
    ]
