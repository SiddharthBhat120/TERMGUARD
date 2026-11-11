"""Export an analysis as a printable PDF report (English)."""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Analysis

INK = colors.HexColor("#1D2B4F")
RISK = {"high": colors.HexColor("#B4332B"), "medium": colors.HexColor("#A86B00"), "low": colors.HexColor("#3F6B57")}
LAWYER = {
    "rental": [
        "You received an eviction notice, or the owner threatens to lock you out or cut water or power.",
        "The deposit is large and the owner refuses to return it or will not give reasons in writing.",
        "The agreement is for more than 11 months and is not registered.",
    ],
    "offer_letter": [
        "The letter has a bond or training-cost recovery of a large amount.",
        "The employer threatens legal action or holds back your relieving letter or final pay.",
        "A non-compete is stopping you from accepting another job.",
    ],
}


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def build_report(a: Analysis) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=f"TermGuard report - {a.filename}")
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], textColor=INK, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=INK, fontSize=13, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13)
    quote = ParagraphStyle("quote", parent=body, leftIndent=8, textColor=colors.HexColor("#3B4560"),
                           fontName="Helvetica-Oblique", borderPadding=4)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#5B6475"))

    story = [
        _p("TermGuard report", h1),
        _p(f"{a.filename}  |  {a.doc_type_label}  |  {len(a.findings)} clauses to question, {len(a.missing)} items not mentioned", small),
        Spacer(1, 6),
        _p(a.disclaimer, small),
    ]
    if a.facts:
        story.append(_p("Key facts (as written)", h2))
        rows = [[_p(f.label, body), _p(f.value, body)] for f in a.facts]
        t = Table(rows, colWidths=[50 * mm, 120 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D1C4")),
                               ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2EA")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)

    story.append(_p("Clauses to question", h2))
    if not a.findings:
        story.append(_p("No checklist items were flagged. Still read the full document before signing.", body))
    for f in a.findings:
        story.append(Paragraph(
            f'<font color="{RISK[f.risk].hexval()}"><b>{f.risk.upper()}</b></font>  <b>{escape(f.name)}</b>'
            f'  <font size="8" color="#5B6475">({escape(f.clause_title)})</font>', body))
        story.append(_p(f"“{f.quote}”", quote))
        story.append(_p(f.explanation, body))
        story.append(_p(f"Ask: {f.question}", body))
        story.append(Spacer(1, 6))

    if a.missing:
        story.append(_p("Not mentioned in the document", h2))
        for m in a.missing:
            story.append(_p(f"{m.name}. {m.why} Ask: {m.question}", body))
            story.append(Spacer(1, 3))

    story.append(_p("When to talk to a lawyer", h2))
    for line in LAWYER.get(a.doc_type, []):
        story.append(_p(f"- {line}", body))
    doc.build(story)
    return buf.getvalue()
