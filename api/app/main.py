"""Jenie Helpdesk AI — HTTP surface.

    GET  /healthz   liveness  — the process is up, nothing else is checked
    GET  /readyz    readiness — database reachable and the index is populated
    GET  /metrics   prometheus
    POST /ask       {"query": "..."} -> {answer, sources[], latency_ms}

Liveness and readiness differ on purpose. A liveness probe that touches the
database turns one Postgres blip into a simultaneous restart of every replica;
readiness is where dependencies belong, because it removes a pod from the load
balancer instead of killing it.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from jenie import embed, rag, store, telemetry
from jenie.config import settings

log = logging.getLogger("jenie.api")


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class SourceOut(BaseModel):
    title: str
    path: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    latency_ms: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    telemetry.configure_logging(settings.log_level)
    # Downloading the embedding model on the first request would make that
    # request a multi-second outlier and pollute the latency SLO. Readiness
    # stays false until this finishes, which is exactly what it is for.
    embed.warm(settings)
    app.state.pool = store.make_pool(settings)
    with app.state.pool.connection() as conn:
        store.ensure_schema(conn, settings)
    log.info("startup complete", extra={"model": settings.llm_model})
    yield
    app.state.pool.close()


app = FastAPI(title="Jenie Helpdesk AI", version="0.1.0", lifespan=lifespan)

# Buckets are part of the SLO contract: kubernetes/apps/jenie/base/slo.yaml
# queries le="2.5". Prometheus does not interpolate between buckets, so a
# threshold with no matching boundary matches nothing and reports healthy.
Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/healthz", "/readyz"],
).instrument(
    app,
    latency_highr_buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    latency_lowr_buckets=(0.1, 0.5, 2.5),
).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, object]:
    try:
        with app.state.pool.connection() as conn:
            n = store.count(conn)
            indexed_at = store.last_indexed(conn)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    if n == 0:
        # An empty index answers nothing useful, so the pod is not ready to
        # serve even though it is perfectly healthy.
        raise HTTPException(status_code=503, detail="index is empty")
    telemetry.INDEX_DOCUMENTS.set(n)
    telemetry.INDEX_LAST_SUCCESS.set(indexed_at)
    return {"status": "ready", "chunks": n}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    with app.state.pool.connection() as conn:
        answer = rag.ask(settings, conn, req.query)
    log.info(
        "ask",
        extra={
            "outcome": answer.outcome,
            "latency_ms": answer.latency_ms,
            "sources": len(answer.sources),
        },
    )
    return AskResponse(
        answer=answer.answer,
        sources=[SourceOut(title=s.title, path=s.path, score=s.score) for s in answer.sources],
        latency_ms=answer.latency_ms,
    )
