"""Model backend selection.

One rule: the backend is chosen by LLM_BASE_URL. Ollama, vLLM, Bedrock through
Floci, and the stub are the same code path with a different URL. No provider
branches, because provider branches are how you end up unable to switch.

Leaving LLM_BASE_URL unset selects the stub, which is what CI uses — tests must
not need a GPU.

TODO (yours): implement.
"""

from jenie.config import Settings


def build_llm(cfg: Settings):
    """Return an OpenAI-compatible LLM client, or the stub when no base URL is set."""
    raise NotImplementedError


def build_embedding(cfg: Settings):
    """Return the embedding client. Batch at cfg.embed_batch_size —
    one HTTP round trip per chunk will dominate indexing time otherwise."""
    raise NotImplementedError


class StubLLM:
    """Deterministic, offline. Echoes the retrieved context so retrieval can be
    tested on its own, and so CI never depends on a model being up."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError
