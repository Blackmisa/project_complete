"""LangChain tools para o agente ReAct da AmazoniaShop."""

from __future__ import annotations

import logging
import random
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool

from src.agent.rag_pipeline import retrieve
from src.features.feature_engineering import clean_text

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        import joblib
        model_path = ROOT / "data" / "processed" / "baseline_model.pkl"
        if model_path.exists():
            _classifier = joblib.load(model_path)
    return _classifier


@tool
def search_kb(query: str) -> str:
    """Busca na base de conhecimento da AmazoniaShop sobre políticas, prazos, pagamentos, trocas e procedimentos. Use sempre que o cliente tiver dúvidas sobre regras ou processos."""
    docs = retrieve(query)
    if not docs:
        return "Nenhum documento relevante encontrado na base de conhecimento."
    parts = [f"[{doc['doc_id']}] {doc['title']}\n{doc['content']}" for doc in docs]
    return "\n\n---\n\n".join(parts)


@tool
def get_order_status(order_id: str) -> str:
    """Consulta o status de um pedido pelo ID (ex: AMZ12345). Use quando o cliente perguntar sobre rastreamento, localização ou prazo de entrega de um pedido específico."""
    statuses = ["Em trânsito", "Entregue", "Aguardando coleta", "Em separação"]
    carriers = ["Correios", "JadLog", "Loggi", "Total Express"]
    status = random.choice(statuses)
    carrier = random.choice(carriers)
    eta = random.randint(1, 7)
    return (
        f"Pedido {order_id}: {status} via {carrier}. "
        f"Previsao de entrega: {eta} dia(s) util(eis)."
    )


@tool
def classify_priority(message: str) -> str:
    """Classifica a categoria e prioridade de um ticket. Use para entender o tipo de problema antes de responder."""
    clf = _get_classifier()
    if clf is None:
        return "Classificador indisponivel. Categoria: indefinida. Prioridade: media."
    cleaned = clean_text(message)
    category = clf.predict([cleaned])[0]
    high_priority = {"reembolso", "produto_defeito", "pagamento_falhou"}
    priority = "alta" if category in high_priority else "media"
    return f"Categoria: {category}. Prioridade: {priority}."


@tool
def escalate_to_human(reason: str) -> str:
    """Escala o atendimento para um agente humano. Use quando o problema for complexo, envolver valores altos, questões legais ou cliente muito insatisfeito."""
    log_path = ROOT / "data" / "processed" / "escalations.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {reason}\n")
    return (
        f"Atendimento escalado para equipe humana. "
        f"Motivo registrado: {reason}. Voce sera contatado em breve."
    )
