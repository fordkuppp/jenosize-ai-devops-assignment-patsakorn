"""pgvector store and hybrid retrieval.

Hybrid rather than vector-only because operations questions are full of exact
tokens — error strings, flag names, CRD kinds — that embeddings blur. Asking
for `externalTrafficPolicy` should find the document containing that literal
word even if the surrounding prose is semantically unlike the question.

The two rankings are fused with Reciprocal Rank Fusion. RRF needs no score
calibration between the two retrievers, which is its whole appeal: comparing a
cosine distance to a ts_rank directly is meaningless.

One consequence worth knowing: RRF is rank-based, so it discards how good the
best match actually was. A nonsense query still produces a rank-1 result and
therefore a high fused score. That is why the raw cosine similarity is carried
alongside and used for the refusal decision — without it the service cannot
tell "this is the best match" from "this is a good match".
"""

import contextlib
from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from jenie.config import Settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id         bigserial PRIMARY KEY,
    path       text    NOT NULL,
    title      text    NOT NULL,
    ordinal    int     NOT NULL,
    content    text    NOT NULL,
    embedding  vector(%(dim)s) NOT NULL,
    tsv        tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    indexed_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (path, ordinal)
);

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
"""

# Fused score normalised so that a chunk ranked first by both retrievers
# scores 1.0. Without this the numbers are ~0.03 and any threshold on them
# reads as arbitrary.
SEARCH = """
WITH semantic AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> %(q)s) AS rank
    FROM chunks ORDER BY embedding <=> %(q)s LIMIT %(cand)s
),
lexical AS (
    SELECT c.id, row_number() OVER (ORDER BY ts_rank_cd(c.tsv, q) DESC) AS rank
    FROM chunks c, plainto_tsquery('english', %(text)s) q
    WHERE c.tsv @@ q
    ORDER BY ts_rank_cd(c.tsv, q) DESC LIMIT %(cand)s
)
SELECT c.path, c.title, c.content,
       (COALESCE(1.0 / (60 + s.rank), 0) + COALESCE(1.0 / (60 + l.rank), 0))
         / (2.0 / 61) AS score,
       1 - (c.embedding <=> %(q)s) AS similarity
FROM chunks c
LEFT JOIN semantic s ON s.id = c.id
LEFT JOIN lexical  l ON l.id = c.id
WHERE s.id IS NOT NULL OR l.id IS NOT NULL
ORDER BY score DESC
LIMIT %(k)s;
"""


@dataclass
class Hit:
    path: str
    title: str
    content: str
    score: float
    similarity: float


def _prepare(conn: psycopg.Connection) -> None:
    """Run on every connection the pool hands out, including replacements."""
    # The extension has to exist before the type can be registered with the
    # adapter — registering first fails with "vector type not found in the
    # database", which reads like a driver problem rather than an ordering
    # one. In the cluster CNPG has already created it via
    # postInitApplicationSQL; this makes a bare Postgres work too.
    with contextlib.suppress(psycopg.errors.InsufficientPrivilege):
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)


def make_pool(cfg: Settings) -> ConnectionPool:
    """A pool, not a long-lived connection.

    A single connection opened at startup dies the first time PostgreSQL
    restarts or fails over, and nothing reopens it: readiness goes 503 and
    stays there until the pod is killed. With a three-instance cluster that
    fails over by design, that is not an edge case.

    `check` validates a connection before handing it out, so a replica
    promotion costs one discarded connection rather than an outage.
    """
    return ConnectionPool(
        cfg.dsn,
        min_size=1,
        max_size=cfg.pg_pool_max,
        kwargs={"autocommit": True},
        configure=_prepare,
        check=ConnectionPool.check_connection,
        open=True,
    )


def connect(cfg: Settings) -> psycopg.Connection:
    """Single connection, for the indexer — a job that runs once and exits."""
    conn = psycopg.connect(cfg.dsn, autocommit=True)
    # The extension has to exist before the type can be registered with the
    # adapter — registering first fails with "vector type not found in the
    # database", which reads like a driver problem rather than an ordering
    # one. In the cluster CNPG has already created it via
    # postInitApplicationSQL; this makes a bare Postgres work too.
    _prepare(conn)
    return conn


def ensure_schema(conn: psycopg.Connection, cfg: Settings) -> None:
    conn.execute(SCHEMA % {"dim": cfg.embedding_dim})


def replace_document(conn: psycopg.Connection, path: str, rows: list[tuple]) -> None:
    """Delete-then-insert per document, so a reindex of a shrunken file does
    not leave orphaned chunks behind."""
    with conn.transaction():
        conn.execute("DELETE FROM chunks WHERE path = %s", (path,))
        conn.cursor().executemany(
            "INSERT INTO chunks (path, title, ordinal, content, embedding)"
            " VALUES (%s, %s, %s, %s, %s)",
            rows,
        )


def count(conn: psycopg.Connection) -> int:
    return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]


def search(
    conn: psycopg.Connection, *, query_vec, text: str, k: int, candidates: int
) -> list[Hit]:
    import numpy as np

    rows = conn.execute(
        SEARCH,
        {"q": np.array(query_vec), "text": text, "k": k, "cand": candidates},
    ).fetchall()
    return [Hit(path=r[0], title=r[1], content=r[2], score=float(r[3]), similarity=float(r[4]))
            for r in rows]
