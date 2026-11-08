"""Chunking and refusal logic — the parts that must hold without a database.

CI runs these with no Postgres, no model server and no GPU, which is the
whole point of the stub backend.
"""

from jenie.chunk import chunk_markdown
from jenie.llm import StubLLM


def test_headings_become_citation_titles():
    chunks = chunk_markdown("# Top\nalpha\n\n## Nested\nbeta\n")
    titles = [c.title for c in chunks]
    assert "Top" in titles
    assert "Top › Nested" in titles, "heading trail is what makes a citation readable"


def test_sections_without_body_are_dropped():
    chunks = chunk_markdown("# Empty\n\n# Real\ncontent here\n")
    assert [c.title for c in chunks] == ["Real"]


def test_oversized_sections_split_with_overlap():
    body = "word " * 400
    chunks = chunk_markdown(f"# Big\n{body}", size=256, overlap=64)
    assert len(chunks) > 1
    assert all(len(c.content) <= 256 for c in chunks)


def test_ordinals_are_unique_and_sequential():
    chunks = chunk_markdown("# A\none\n\n# B\ntwo\n\n# C\nthree\n")
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))


def test_stub_declines_without_context():
    out = StubLLM().complete("anything", [])
    assert "don't have" in out.text


def test_stub_is_extractive_not_generative():
    # It must quote retrieved text verbatim. A fluent stub would hide
    # retrieval failures behind plausible prose.
    out = StubLLM().complete("q", ["the externalTrafficPolicy is Cluster"])
    assert "externalTrafficPolicy is Cluster" in out.text
