"""Prometheus metrics and structured JSON logging.

Retrieval and generation are deliberately separate histograms. Blended into one
"request duration" you cannot tell a slow vector search from a slow model, which
is the first question anyone asks when /ask gets slow.
"""

import logging
import sys

from prometheus_client import Counter, Histogram
from pythonjsonlogger import json as jsonlogger

RETRIEVAL_SECONDS = Histogram(
    "rag_retrieval_duration_seconds",
    "Time spent retrieving candidate chunks",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

GENERATION_SECONDS = Histogram(
    "rag_generation_duration_seconds",
    "Time spent in the LLM call",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

TOKENS = Counter(
    "rag_tokens_total",
    "Tokens consumed, by kind",
    ["kind"],  # prompt | completion
)

COST_USD = Counter(
    "rag_cost_usd_total",
    "Estimated spend, priced from configured per-1k rates",
)

ASK_ERRORS = Counter(
    "rag_ask_errors_total",
    "Failed /ask requests, by stage",
    ["stage"],  # retrieval | generation
)

INDEXED_DOCUMENTS = Counter(
    "rag_indexed_documents_total",
    "Documents written to the vector store by the worker",
)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "ts", "levelname": "level"},
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
