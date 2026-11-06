"""Jenie Helpdesk AI — HTTP surface.

Endpoints:
    GET  /healthz   liveness  — process is up, no dependency checks
    GET  /readyz    readiness — database reachable, index present
    GET  /metrics   prometheus
    POST /ask       {"query": "..."} -> {answer, sources[], latency_ms}

Liveness and readiness are deliberately different. A liveness probe that checks
the database restarts every pod in the cluster when the database blips.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from jenie.config import settings
from jenie.telemetry import configure_logging


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class SourceOut(BaseModel):
    title: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    latency_ms: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = settings()
    configure_logging(cfg.log_level)
    # TODO: build the index once here and hang it off app.state —
    #       rebuilding per request will dominate your p95.
    yield
    # TODO: close the connection pool so in-flight requests drain cleanly.


app = FastAPI(title="Jenie Helpdesk AI", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    # TODO: SELECT 1, and assert the chunks table is non-empty.
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    started = time.perf_counter()
    # TODO: call jenie.rag.ask(), record the phase histograms, add tokens + cost.
    raise NotImplementedError
