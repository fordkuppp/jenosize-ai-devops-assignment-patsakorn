"""Embeddings — fastembed, ONNX, CPU.

Deliberately not sentence-transformers: that drags in torch for a 130MB model
we run on CPU, and the image size shows up in every pull on every node.

The model is loaded lazily and once. Constructing it downloads weights on
first use, so doing that at import time would make the readiness probe race
a network fetch.
"""

from functools import lru_cache

from fastembed import TextEmbedding

from jenie.config import Settings


@lru_cache(maxsize=1)
def _model(name: str) -> TextEmbedding:
    return TextEmbedding(model_name=name)


def embed_documents(cfg: Settings, texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _model(cfg.embedding_model).embed(texts)]


def embed_query(cfg: Settings, text: str) -> list[float]:
    # bge models are trained with an asymmetric query prefix; omitting it
    # measurably degrades retrieval, and the failure is silent — results come
    # back, they are just worse.
    prefixed = f"Represent this sentence for searching relevant passages: {text}"
    return next(iter(_model(cfg.embedding_model).embed([prefixed]))).tolist()


def warm(cfg: Settings) -> None:
    """Force the download and first inference, so readiness reflects reality."""
    embed_query(cfg, "warmup")
