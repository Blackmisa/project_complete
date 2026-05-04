"""FastAPI — assistente de atendimento AmazoniaShop."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

from src.agent.rag_pipeline import index_knowledge_base
from src.agent.react_agent import run_agent
from src.security.guardrails import InputGuardrail, OutputGuardrail

load_dotenv()
logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter("chat_requests_total", "Total de requests ao /chat")
REQUEST_ERRORS = Counter("chat_errors_total", "Total de erros no /chat")
REQUEST_LATENCY = Histogram("chat_latency_seconds", "Latencia do /chat em segundos")

_input_guard = InputGuardrail()
_output_guard = OutputGuardrail()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Indexando knowledge base no Qdrant...")
    try:
        count = index_knowledge_base()
        logger.info("KB pronta: %d documentos indexados.", count)
    except Exception as exc:
        logger.warning("Falha ao indexar KB na inicializacao: %s", exc)
    yield


app = FastAPI(
    title="AmazoniaShop Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    answer: str
    trace_id: str
    used_tools: list[str]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    REQUEST_COUNT.inc()
    session_id = request.session_id or str(uuid.uuid4())
    try:
        _input_guard.check(request.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    with REQUEST_LATENCY.time():
        try:
            result = run_agent(request.message, session_id=session_id)
        except Exception as exc:
            REQUEST_ERRORS.inc()
            logger.exception("Erro no agente: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc))
    return ChatResponse(
        answer=_output_guard.sanitize(result["answer"]),
        trace_id=session_id,
        used_tools=result["used_tools"],
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
