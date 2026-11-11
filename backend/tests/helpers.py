"""Build an ExtractedDoc from plain lines, so splitter tests do not need PDFs."""
from app.models import ExtractedDoc, Line, PageInfo, Rect


def doc_from_lines(lines: list[str], blocks: list[int] | None = None) -> ExtractedDoc:
    out, parts, offset = [], [], 0
    for i, text in enumerate(lines):
        block = blocks[i] if blocks else i
        out.append(Line(page=0, block=block, text=text, start=offset, end=offset + len(text),
                        rect=Rect(page=0, x0=50, y0=50 + i * 14, x1=500, y1=62 + i * 14)))
        parts.append(text)
        offset += len(text) + 1
    return ExtractedDoc(text="\n".join(parts), lines=out, pages=[PageInfo(width=595, height=842)])
