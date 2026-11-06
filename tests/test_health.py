"""Placeholder so `pytest` has something to run before the app exists.

TODO: replace with real tests —
  - retrieval returns the expected document for a known query (testcontainers
    postgres + the stub LLM, so no GPU is needed in CI)
  - /ask rejects an empty query with 422
  - /readyz fails when the chunks table is empty
"""


def test_placeholder() -> None:
    assert True
