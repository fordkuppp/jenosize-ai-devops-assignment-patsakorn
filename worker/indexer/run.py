"""Indexer — walks the corpus, chunks it, embeds it, writes it to pgvector.

Runs to completion and exits; it is a job, not a service. For a corpus this size
a single pass is correct. Incremental reindexing is noted in the README as the
next step rather than built, because 15 files do not justify change detection.

TODO (yours): implement.
"""

import logging

from jenie.config import settings
from jenie.telemetry import configure_logging


def main() -> None:
    cfg = settings()
    configure_logging(cfg.log_level)
    log = logging.getLogger("indexer")

    # TODO:
    #   SimpleDirectoryReader(cfg.data_dir, required_exts=[".md"])
    #   -> MarkdownNodeParser (keeps section headings, which become citations)
    #   -> embed in batches of cfg.embed_batch_size
    #   -> VectorStoreIndex.from_documents(..., storage_context=...)
    #   increment telemetry.INDEXED_DOCUMENTS as you go
    log.info("indexing", extra={"data_dir": cfg.data_dir})
    raise NotImplementedError


if __name__ == "__main__":
    main()
