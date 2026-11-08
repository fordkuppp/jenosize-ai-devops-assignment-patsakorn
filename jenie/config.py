"""Configuration. Every knob is an environment variable; nothing is hardcoded.

Two rules worth stating because they shaped the rest of the code:

1. The model backend is selected by LLM_BASE_URL alone. Leaving it unset gives
   the deterministic stub, which is what CI uses — the pipeline must never need
   a GPU. Pointing it at vLLM or Ollama changes no code.
2. The database is assembled from the standard PG* variables, because that is
   what CloudNativePG publishes in its generated secret. Accepting
   DATABASE_URL as an override keeps docker-compose simple.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── database ────────────────────────────────────────────────────────
    pghost: str = "localhost"
    pgport: int = 5432
    pguser: str = "jenie"
    pgpassword: str = ""
    pgdatabase: str = "jenie"
    database_url: str | None = None

    # ── embeddings ──────────────────────────────────────────────────────
    # ONNX on CPU. 384 dimensions, ~130MB. The dimension is part of the
    # table schema, so changing the model means reindexing — not a runtime
    # switch, which is why it lives here rather than being inferred.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # ── inference ───────────────────────────────────────────────────────
    llm_base_url: str | None = None
    llm_model: str = "stub"
    llm_api_key: str = "not-needed-locally"
    llm_timeout_seconds: float = 30.0
    # Priced per million tokens; only ever a cost *proxy*, which is what the
    # brief asks for. Zero for the stub so local runs do not invent spend.
    llm_cost_per_mtok_in: float = 0.0
    llm_cost_per_mtok_out: float = 0.0

    # ── chunking and retrieval ──────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5
    retrieval_candidates: int = 30
    # Cosine similarity, not the fused RRF score. RRF is rank-based and so a
    # nonsense query still yields a rank-1 result with a high fused score —
    # it cannot distinguish "best match" from "good match". The raw
    # similarity can, and this is the line below which the service refuses
    # rather than inventing an answer. Tuned against scripts/queries.yaml.
    retrieval_min_similarity: float = 0.55

    data_dir: str = "data"
    log_level: str = "info"

    @property
    def dsn(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
