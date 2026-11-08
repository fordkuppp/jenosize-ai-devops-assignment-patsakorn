"""Markdown-aware chunking.

Splitting on headings rather than a fixed character window, because the
heading is what makes a citation readable: "Runbook — retrieval latency ›
If search" tells the reader where the answer came from, and an offset does
not. Oversized sections are then split with overlap so a paragraph straddling
a boundary still matches.
"""

import re
from dataclasses import dataclass

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    title: str
    content: str
    ordinal: int


def chunk_markdown(text: str, *, size: int = 512, overlap: int = 64) -> list[Chunk]:
    sections: list[tuple[str, list[str]]] = []
    trail: list[str] = []
    body: list[str] = []
    title = ""

    for line in text.splitlines():
        m = HEADING.match(line)
        if not m:
            body.append(line)
            continue
        if body:
            sections.append((title, body))
        depth = len(m.group(1))
        trail = trail[: depth - 1] + [m.group(2).strip()]
        title = " › ".join(trail)
        body = []
    if body:
        sections.append((title, body))

    out: list[Chunk] = []
    for heading, lines in sections:
        content = "\n".join(lines).strip()
        if not content:
            continue
        for piece in _split(content, size, overlap):
            out.append(Chunk(title=heading or "(untitled)", content=piece, ordinal=len(out)))
    return out


def _split(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    step = max(size - overlap, 1)
    return [text[i : i + size] for i in range(0, len(text), step) if text[i : i + size].strip()]
