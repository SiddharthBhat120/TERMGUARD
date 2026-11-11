"""Build the synthetic sample PDFs and the seed evaluation labels.

    python samples/generate_samples.py

Writes samples/public/*.pdf, eval/labels/*.json and backend/tests/fixtures/*.pdf.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from documents import DOCS, Doc  # noqa: E402

PUBLIC = HERE / "public"
LABELS = ROOT / "eval" / "labels"
FIXTURES = ROOT / "backend" / "tests" / "fixtures"

TITLE = ParagraphStyle("t", fontName="Times-Bold", fontSize=15, alignment=1, spaceAfter=14)
BODY = ParagraphStyle("b", fontName="Times-Roman", fontSize=11, leading=15, spaceAfter=7, alignment=4)
HEAD = ParagraphStyle("h", fontName="Times-Bold", fontSize=11, leading=15, spaceBefore=6, spaceAfter=2)


def build_pdf(doc: Doc, path: Path) -> None:
    story = [Paragraph(escape(doc.title), TITLE)]
    for line in doc.intro:
        story.append(Paragraph(escape(line), BODY))
    story.append(Spacer(1, 4))
    for i, c in enumerate(doc.clauses, 1):
        text = escape(c.text)
        if doc.style in ("numbered", "letter"):
            story.append(Paragraph(f"<b>{i}. {escape(c.heading)}.</b> {text}", BODY))
        elif doc.style == "clause":
            story.append(Paragraph(f"Clause {i}: {escape(c.heading)}", HEAD))
            story.append(Paragraph(text, BODY))
        elif doc.style == "caps":
            story.append(Paragraph(escape(c.heading.upper()), HEAD))
            story.append(Paragraph(text, BODY))
        else:  # plain paragraphs, no headings
            story.append(Paragraph(text, BODY))
    story.append(Spacer(1, 8))
    for line in doc.outro:
        story.append(Paragraph(escape(line), BODY))
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=24 * mm, rightMargin=24 * mm, topMargin=22 * mm,
                      bottomMargin=22 * mm, title=doc.title, author="TermGuard sample (synthetic)").build(story)


def to_scanned(path: Path, dpi: int = 200) -> None:
    """Replace a PDF with an image-only copy (no text layer), like a phone scan."""
    src = pymupdf.open(path)
    out = pymupdf.open()
    for page in src:
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        new = out.new_page(width=page.rect.width, height=page.rect.height)
        new.insert_image(new.rect, pixmap=pix)
    src.close()
    data = out.tobytes(deflate=True)
    out.close()
    path.write_bytes(data)


def write_labels(doc: Doc) -> None:
    rows = [{"clause_start": c.text[:60], "labels": c.labels} for c in doc.clauses]
    (LABELS / f"{doc.name}.json").write_text(json.dumps(
        {"document": f"{doc.name}.pdf", "kind": doc.kind, "labelled_by": "seed (synthetic sample)",
         "clauses": rows}, indent=2), encoding="utf-8")


def build_other(path: Path) -> None:
    other = Doc(name="college_notice", kind="other", style="plain", title="Notice: Library Timings",
                intro=[], clauses=[
                    __import__("documents").C("", "The central library will remain open from 8 AM to 8 PM on all "
                                              "working days during the examination period."),
                    __import__("documents").C("", "Students are requested to carry their ID cards and return "
                                              "borrowed books before the end of the semester."),
                ])
    build_pdf(other, path)


def main() -> None:
    for d in (PUBLIC, LABELS, FIXTURES):
        d.mkdir(parents=True, exist_ok=True)
    for doc in DOCS:
        path = PUBLIC / f"{doc.name}.pdf"
        build_pdf(doc, path)
        if doc.scanned:
            to_scanned(path)
        write_labels(doc)
        print("wrote", path.relative_to(ROOT))
    build_other(FIXTURES / "other_document.pdf")
    for name in ("rental_bengaluru_strict", "offer_startup_bond", "rental_scanned_copy", "rental_plain_letter_style"):
        (FIXTURES / f"{name}.pdf").write_bytes((PUBLIC / f"{name}.pdf").read_bytes())
    print("fixtures ready")


if __name__ == "__main__":
    main()
