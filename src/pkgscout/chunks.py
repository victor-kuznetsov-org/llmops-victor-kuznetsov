"""Split a package's Markdown description into chunks."""

import re

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def split_by_headings(markdown: str | None, min_chars: int = 40) -> list[dict]:
    """Split Markdown at its headings (ignoring '#' lines inside code fences).

    Each chunk is {"heading", "text"}; the text starts with its heading line. Text before the
    first heading is a chunk with an empty heading. Chunks shorter than min_chars are merged
    into the previous chunk.
    """
    if not markdown:
        return []
    sections: list[list] = [["", []]]
    in_fence = False
    for line in markdown.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            sections.append([m.group(2).strip(), [line]])
        else:
            sections[-1][1].append(line)
    chunks: list[dict] = []
    for heading, lines in sections:
        text = "\n".join(lines).strip()
        if not text:
            continue
        if chunks and len(text) < min_chars:
            chunks[-1]["text"] += "\n\n" + text
        else:
            chunks.append({"heading": heading, "text": text})
    return chunks


def fixed_windows(text: str | None, size: int = 800, overlap: int = 100) -> list[str]:
    """Split text in windows of `size` characters, each overlapping the previous by `overlap`."""
    if not text:
        return []
    step = size - overlap
    return [text[i : i + size] for i in range(0, max(len(text) - overlap, 1), step)]
