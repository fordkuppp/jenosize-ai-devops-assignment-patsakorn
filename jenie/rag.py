"""Retrieve, then generate.

The two phases are timed separately and recorded on separate histograms with
separate SLOs, because the platform owns retrieval and the model owns
generation. Blended, a slow model and a slow index look identical.
"""

import time
from dataclasses import dataclass

from jenie import embed, store, telemetry
from jenie.config import Settings
from jenie.llm import build_llm

PROMPT = """Answer the question using only the context below.

Context:
{context}

Question: {question}
"""


@dataclass
class Source:
    title: str
    path: str
    score: float


@dataclass
class Answer:
    answer: str
    sources: list[Source]
    latency_ms: int
    outcome: str


def ask(cfg: Settings, conn, query: str) -> Answer:
    started = time.perf_counter()

    try:
        t0 = time.perf_counter()
        qvec = embed.embed_query(cfg, query)
        telemetry.RETRIEVAL_SECONDS.labels(stage="embed").observe(time.perf_counter() - t0)

        t0 = time.perf_counter()
        hits = store.search(
            conn,
            query_vec=qvec,
            text=query,
            k=cfg.retrieval_top_k,
            candidates=cfg.retrieval_candidates,
        )
        telemetry.RETRIEVAL_SECONDS.labels(stage="search").observe(time.perf_counter() - t0)
    except Exception:
        telemetry.ERRORS.labels(stage="retrieval").inc()
        raise

    telemetry.DOCUMENTS_RETRIEVED.observe(len(hits))
    best = max((h.similarity for h in hits), default=0.0)
    telemetry.RETRIEVAL_SCORE.observe(best)

    # Refusing an out-of-corpus question is correct behaviour, not a failure.
    # It is counted separately so a release that starts refusing everything is
    # visible — that regression returns 200s quickly and is invisible to both
    # error rate and latency.
    if not hits or best < cfg.retrieval_min_similarity:
        telemetry.ANSWERS.labels(outcome="refused" if hits else "no_context").inc()
        telemetry.REQUEST_SECONDS.labels(model=cfg.llm_model).observe(
            time.perf_counter() - started
        )
        return Answer(
            answer=(
                "I don't have anything in the knowledge base that answers that. "
                "Nothing retrieved was close enough to be worth quoting."
            ),
            sources=[],
            latency_ms=int((time.perf_counter() - started) * 1000),
            outcome="refused",
        )

    context = [f"[{h.title}]\n{h.content}" for h in hits]
    try:
        t0 = time.perf_counter()
        completion = build_llm(cfg).complete(
            PROMPT.format(context="\n\n".join(context), question=query), context
        )
        telemetry.GENERATION_SECONDS.labels(model=cfg.llm_model).observe(
            time.perf_counter() - t0
        )
    except Exception:
        telemetry.ERRORS.labels(stage="generation").inc()
        raise

    telemetry.TOKENS.labels(kind="prompt", model=cfg.llm_model).inc(completion.prompt_tokens)
    telemetry.TOKENS.labels(kind="completion", model=cfg.llm_model).inc(
        completion.completion_tokens
    )
    telemetry.COST.labels(model=cfg.llm_model).inc(
        completion.prompt_tokens / 1e6 * cfg.llm_cost_per_mtok_in
        + completion.completion_tokens / 1e6 * cfg.llm_cost_per_mtok_out
    )
    telemetry.ANSWERS.labels(outcome="answered").inc()

    elapsed = time.perf_counter() - started
    telemetry.REQUEST_SECONDS.labels(model=cfg.llm_model).observe(elapsed)

    return Answer(
        answer=completion.text,
        sources=[Source(title=h.title, path=h.path, score=round(h.score, 4)) for h in hits],
        latency_ms=int(elapsed * 1000),
        outcome="answered",
    )
