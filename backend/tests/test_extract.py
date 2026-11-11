import pytest

from app.doctype import detect_doc_type
from app.extract import extract_pdf, ocr_available, rects_for_span


def test_text_pdf_keeps_positions(fixture_bytes):
    doc = extract_pdf(fixture_bytes("rental_bengaluru_strict.pdf"))
    assert "lock-in period of 11 months" in doc.text.replace("\n", " ")
    assert doc.pages and doc.pages[0].width > 500
    for line in doc.lines:
        assert doc.text[line.start:line.end] == line.text
        assert line.rect.x1 > line.rect.x0 and line.rect.y1 > line.rect.y0
    assert not any(p.ocr for p in doc.pages)


def test_span_to_rects_narrows_partial_lines(fixture_bytes):
    doc = extract_pdf(fixture_bytes("rental_bengaluru_strict.pdf"))
    line = max(doc.lines, key=lambda l: len(l.text))
    full = rects_for_span(doc.lines, line.start, line.end)[0]
    half = rects_for_span(doc.lines, line.start, line.start + len(line.text) // 2)[0]
    assert half.x1 < full.x1 and half.x0 == pytest.approx(full.x0)


@pytest.mark.skipif(not ocr_available(), reason="Tesseract not installed")
def test_scanned_pdf_uses_ocr(fixture_bytes):
    doc = extract_pdf(fixture_bytes("rental_scanned_copy.pdf"))
    assert all(p.ocr for p in doc.pages)
    flat = " ".join(doc.text.split()).lower()
    assert "security deposit" in flat and "three months" in flat
    assert doc.lines and doc.lines[0].rect.y1 > doc.lines[0].rect.y0


def test_doc_type_detection(fixture_bytes):
    assert detect_doc_type(extract_pdf(fixture_bytes("rental_bengaluru_strict.pdf")).text)[0] == "rental"
    assert detect_doc_type(extract_pdf(fixture_bytes("offer_startup_bond.pdf")).text)[0] == "offer_letter"
    assert detect_doc_type(extract_pdf(fixture_bytes("other_document.pdf")).text)[0] == "other"
