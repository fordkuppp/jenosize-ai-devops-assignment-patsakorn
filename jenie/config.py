"""Configuration. Every knob is an environment variable; nothing is hardcoded.

The backend selection rule: ollama, vLLM, Bedrock-via-Floci and the offline stub
are all reached through the same OpenAI-compatible interface. Swapping them is a
change to LLM_BASE_URL, never a change to code.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # database
    database_url: str = "postgresql://jenie:change-me-locally@postgres:5432/jenie"
    pg_table: str = "chunks"

    # inference (OpenAI-compatible)
    llm_base_url: str | None = None  # unset -> deterministic stub, used in CI
    llm_model: str = "qwen3.5:9b"
    llm_api_key: str = "not-needed-locally"

    embed_base_url: str | None = None
    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768
    embed_batch_size: int = 32

    # retrieval
    retrieval_top_k: int = 5
    retrieval_candidates: int = 50
    hybrid_search: bool = True

    # chunking
    chunk_size: int = 1024
    chunk_overlap: int = 128

    # corpus
    data_dir: str = "/data"

    # cost proxy — real pricing is per-model; these are config, not constants
    cost_per_1k_prompt_usd: float = 0.0005
    cost_per_1k_completion_usd: float = 0.0015

    # ops
    log_level: str = "INFO"
    shutdown_grace_seconds: int = 20


@lru_cache
def settings() -> Settings:
    return Settings()
