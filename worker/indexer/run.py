"""Indexer — read the corpus, chunk, embed, upsert.

Runs to completion and exits. It is a Job, not a Deployment: indexing is
bursty and CPU-heavy while serving is steady and latency-sensitive, and
sharing a process means one degrades the other.
"""

import logging
import pathlib
import sys
import time

from jenie import chunk, embed, store, telemetry
from jenie.config import settings

log = logging.getLogger("jenie.indexer")


def main() -> int:
    telemetry.configure_logging(settings.log_level)
    root = pathlib.Path(settings.data_dir)
    files = sorted(root.rglob("*.md"))
    if not files:
        log.error("no documents found", extra={"dir": str(root)})
        return 1

    conn = store.connect(settings)
    store.ensure_schema(conn, settings)

    total = 0
    for path in files:
        rel = str(path.relative_to(root))
        chunks = chunk.chunk_markdown(
            path.read_text(encoding="utf-8"),
            size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        if not chunks:
            log.warning("no chunks produced", extra={"path": rel})
            continue
        # Batched: one embedding call per chunk would dominate the run.
        # Heading plus body. The heading trail is often the most
        # discriminating text in an operations document — dropping it let a
        # table that merely mentions "backup retention" outrank the section
        # actually titled "The gap".
        vectors = embed.embed_documents(
            settings, [f"{c.title}\n\n{c.content}" for c in chunks]
        )
        store.replace_document(
            conn,
            rel,
            [(rel, c.title, c.ordinal, c.content, v) for c, v in zip(chunks, vectors, strict=True)],
        )
        total += len(chunks)
        log.info("indexed", extra={"path": rel, "chunks": len(chunks)})

    n = store.count(conn)
    telemetry.INDEX_DOCUMENTS.set(n)
    telemetry.INDEX_LAST_SUCCESS.set(time.time())
    log.info("done", extra={"documents": len(files), "chunks": total, "total_in_index": n})
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
