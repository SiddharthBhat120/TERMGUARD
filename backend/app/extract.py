"""Phase 1: get text out of a PDF and remember where every line sits on the page.

Text pages use PyMuPDF's text layer. Pages with (almost) no text but with images are
treated as scanned and sent to Tesseract OCR, if it is installed.
"""
from __future__ import annotations

import io
import shutil

import pymupdf

from .config import settings
from .models import ExtractedDoc, Line, PageInfo, Rect

MIN_TEXT_CHARS = 25  # fewer characters than this on a page = probably a scan
OCR_DPI = 300


def ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    if settings.tesseract_cmd:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        return True
    return shutil.which("tesseract") is not None


def _text_lines(page: pymupdf.Page, page_no: int) -> list[tuple[int, str, Rect]]:
    out: list[tuple[int, str, Rect]] = []
    data = page.get_text("dict", sort=True)
    for b_idx, block in enumerate(data.get("blocks", [])):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line.get("spans", []))
            text = " ".join(text.split())
            if not text:
                continue
            x0, y0, x1, y1 = line["bbox"]
            out.append((b_idx, text, Rect(page=page_no, x0=x0, y0=y0, x1=x1, y1=y1)))
    return out


def _ocr_lines(page: pymupdf.Page, page_no: int) -> list[tuple[int, str, Rect]]:
    import pytesseract
    from PIL import Image

    pix = page.get_pixmap(dpi=OCR_DPI)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    scale = 72.0 / OCR_DPI
    groups: dict[tuple[int, int, int], list[int]] = {}
    for i, word in enumerate(data["text"]):
        if not str(word).strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        groups.setdefault(key, []).append(i)
    out: list[tuple[int, str, Rect]] = []
    for (block, par, _line), idxs in sorted(groups.items(), key=lambda kv: (data["top"][kv[1][0]], data["left"][kv[1][0]])):
        words = [str(data["text"][i]).strip() for i in idxs]
        x0 = min(data["left"][i] for i in idxs) * scale
        y0 = min(data["top"][i] for i in idxs) * scale
        x1 = max(data["left"][i] + data["width"][i] for i in idxs) * scale
        y1 = max(data["top"][i] + data["height"][i] for i in idxs) * scale
        out.append((block * 100 + par, " ".join(words), Rect(page=page_no, x0=x0, y0=y0, x1=x1, y1=y1)))
    return out


def extract_pdf(data: bytes) -> ExtractedDoc:
    """Return the document text, each line's position, and page sizes."""
    doc = pymupdf.open(stream=data, filetype="pdf")
    lines: list[Line] = []
    pages: list[PageInfo] = []
    parts: list[str] = []
    offset = 0
    ocr_missing = False
    block_base = 0
    can_ocr = ocr_available()
    for page_no, page in enumerate(doc):
        raw = _text_lines(page, page_no)
        is_scan = sum(len(t) for _, t, _ in raw) < MIN_TEXT_CHARS and bool(page.get_images())
        used_ocr = False
        if is_scan:
            if can_ocr:
                raw = _ocr_lines(page, page_no)
                used_ocr = True
            else:
                ocr_missing = True
        pages.append(PageInfo(width=page.rect.width, height=page.rect.height, ocr=used_ocr))
        max_block = 0
        for block, text, rect in raw:
            start = offset
            end = start + len(text)
            lines.append(Line(page=page_no, block=block_base + block, text=text, start=start, end=end, rect=rect))
            parts.append(text)
            offset = end + 1  # the "\n" joiner
            max_block = max(max_block, block)
        block_base += max_block + 1
    doc.close()
    return ExtractedDoc(text="\n".join(parts), lines=lines, pages=pages, ocr_missing=ocr_missing)


def rects_for_span(lines: list[Line], start: int, end: int) -> list[Rect]:
    """Rectangles of every line that overlaps the character span [start, end)."""
    out: list[Rect] = []
    for line in lines:
        if line.end <= start or line.start >= end:
            continue
        r = line.rect
        length = max(1, line.end - line.start)
        width = r.x1 - r.x0
        a = (max(start, line.start) - line.start) / length
        b = (min(end, line.end) - line.start) / length
        # Character positions are an approximation of x positions, which is close
        # enough for a highlighter; full lines keep their exact box.
        out.append(Rect(page=r.page, x0=r.x0 + width * a, y0=r.y0, x1=r.x0 + width * b, y1=r.y1))
    return out
