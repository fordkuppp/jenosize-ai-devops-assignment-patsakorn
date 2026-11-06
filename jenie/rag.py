"""Index construction and querying.

LlamaIndex owns ingestion, chunking, embedding and retrieval. This module is the
seam between it and the service: it builds the objects once, and exposes the two
operations the platform cares about.

TODO (yours): implement. The shape below is the contract the API depends on.
"""

from dataclasses import dataclass

from jenie.config import Settings


@dataclass
class Source:
    title: str
    path: str
    score: float


@dataclass
class Answer:
    answer: str
    sources: list[Source]
    retrieval_seconds: float
    generation_seconds: float
    prompt_tokens: int
    completion_tokens: int


def build_vector_store(cfg: Settings):
    """PGVectorStore against the configured database.

    Set hybrid_search=True and text_search_config="english" so Postgres keeps a
    tsvector alongside the embedding — semantic search alone misses exact tokens
    (error codes, flag names, hostnames) that operations questions are full of.
    """
    raise NotImplementedError


def build_index(cfg: Settings):
    """VectorStoreIndex over the store above, wired to the embedding model."""
    raise NotImplementedError


def ask(cfg: Settings, query: str) -> Answer:
    """Retrieve, then generate.

    Time the two phases separately and record them on the histograms in
    jenie.telemetry — that split is the point of the dashboard.
    """
    raise NotImplementedError
