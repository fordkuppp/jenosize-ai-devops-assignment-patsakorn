"""Model backend selection.

One rule: the backend is chosen by LLM_BASE_URL. vLLM, Ollama, and anything
else speaking the OpenAI chat-completions API are the same code path with a
different URL. There are no provider branches, because provider branches are
how a service ends up unable to switch.

Unset selects the stub — deterministic, offline, and what CI uses. Tests must
never need a GPU.
"""

from dataclasses import dataclass

import httpx

from jenie.config import Settings

SYSTEM = (
    "You answer questions about this platform using only the provided context. "
    "If the context does not contain the answer, say so plainly. Cite nothing "
    "you were not given."
)


@dataclass
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int


def _approx_tokens(text: str) -> int:
    # Good enough for a cost *proxy*, which is what is being asked for. A real
    # tokenizer would be exact and would also have to match whichever model is
    # behind LLM_BASE_URL, which defeats the point of not branching per
    # provider.
    return max(1, len(text) // 4)


class StubLLM:
    """Extractive, not generative.

    It returns the retrieved passage rather than paraphrasing it. That makes
    every evaluation result attributable to retrieval, which is the half the
    platform actually controls — a fluent stub would hide retrieval failures
    behind plausible prose.
    """

    def complete(self, prompt: str, context: list[str]) -> Completion:
        if not context:
            text = "I don't have anything in the knowledge base that answers that."
        else:
            best = context[0].strip()
            text = best if len(best) <= 600 else best[:600].rsplit(" ", 1)[0] + "…"
        return Completion(text, _approx_tokens(prompt), _approx_tokens(text))


class OpenAICompatLLM:
    def __init__(self, cfg: Settings) -> None:
        self._cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.llm_base_url.rstrip("/"),
            timeout=cfg.llm_timeout_seconds,
            headers={"Authorization": f"Bearer {cfg.llm_api_key}"},
        )

    def complete(self, prompt: str, context: list[str]) -> Completion:
        r = self._client.post(
            "/chat/completions",
            json={
                "model": self._cfg.llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            },
        )
        r.raise_for_status()
        body = r.json()
        usage = body.get("usage") or {}
        return Completion(
            text=body["choices"][0]["message"]["content"].strip(),
            prompt_tokens=usage.get("prompt_tokens") or _approx_tokens(prompt),
            completion_tokens=usage.get("completion_tokens") or 0,
        )


def build_llm(cfg: Settings):
    return OpenAICompatLLM(cfg) if cfg.llm_base_url else StubLLM()
