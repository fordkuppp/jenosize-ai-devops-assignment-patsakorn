"""Prometheus metrics and structured JSON logging.

The metric names here are a contract, not an implementation detail: they are
referenced by the Sloth SLO definitions, the PrometheusRule alerts and the
Flagger metric templates. Renaming one breaks three files that will not fail
loudly — the queries simply match nothing and report healthy.

Retrieval and generation are separate histograms on purpose. Blended into one
duration you cannot tell a slow vector search from a slow model, which is the
first question anyone asks when /ask gets slow. They also have separate SLOs
for the same reason: the platform owns retrieval, the model owns generation.
"""

import logging
import sys

from prometheus_client import Counter, Gauge, Histogram
from pythonjsonlogger import json as jsonlogger

# Bucket boundaries are part of the SLO contract. kubernetes/apps/jenie/base/
# slo.yaml queries le="0.5" for retrieval and le="2.5" end to end; Prometheus
# cannot interpolate, so a threshold without a matching boundary silently
# measures nothing.
RETRIEVAL_SECONDS = Histogram(
    "rag_retrieval_duration_seconds",
    "Time spent retrieving candidate chunks",
    ["stage"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

GENERATION_SECONDS = Histogram(
    "rag_generation_duration_seconds",
    "Time spent in the model call",
    ["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

REQUEST_SECONDS = Histogram(
    "rag_request_duration_seconds",
    "End to end /ask duration",
    ["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

DOCUMENTS_RETRIEVED = Histogram(
    "rag_documents_retrieved",
    "Chunks returned per query",
    buckets=(0, 1, 2, 3, 5, 8, 13),
)

# Drift signal. The JD asks for one, and the top-1 similarity distribution is
# the cheapest honest proxy: if it shifts, what the index can answer changed.
RETRIEVAL_SCORE = Histogram(
    "rag_retrieval_score",
    "Fused score of the best-matching chunk",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0),
)

TOKENS = Counter("rag_tokens_total", "Tokens consumed", ["kind", "model"])
COST = Counter("rag_cost_usd_total", "Simulated spend", ["model"])

# outcome = answered | refused | no_context.
# Refusals are correct behaviour for out-of-corpus questions, so this is a
# regression signal rather than an error count — a release that starts
# refusing returns 200s quickly and is invisible to latency and error rate.
ANSWERS = Counter("rag_answers_total", "Answers by outcome", ["outcome"])
ERRORS = Counter("rag_errors_total", "Failures by pipeline stage", ["stage"])

INDEX_DOCUMENTS = Gauge("rag_index_documents", "Chunks currently indexed")
INDEX_LAST_SUCCESS = Gauge(
    "rag_index_last_success_timestamp_seconds",
    "Unix time of the last successful indexing run",
)


def configure_logging(level: str = "info") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "ts"},
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
