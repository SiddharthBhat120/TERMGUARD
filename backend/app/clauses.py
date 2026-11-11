"""Phase 2: split the document into clauses.

Rules first (numbering such as "1.", "2.1", "(a)", "Clause 5", and ALL-CAPS headings).
If a document has almost no numbering, we fall back to paragraphs (PDF text blocks),
and, when an LLM is configured, the caller may ask it to group paragraphs instead.
"""
from __future__ import annotations

import re

from .extract import rects_for_span
from .models import Clause, ExtractedDoc, Line

NUMBERED = re.compile(r"^\s*(?P<num>\d{1,2}(?:\.\d{1,2}){0,2})[.)]?\s+(?P<rest>\S.*)$")
LETTERED = re.compile(r"^\s*\((?P<num>[a-z]|[ivx]{1,4})\)\s+(?P<rest>\S.*)$")
KEYWORD = re.compile(r"^\s*(?:clause|article|section)\s+(?P<num>\d{1,2}(?:\.\d{1,2})?)\s*[:.\-]?\s*(?P<rest>.*)$", re.I)
CAPS = re.compile(r"^[A-Z][A-Z &/,'\-()]{3,60}:?$")

MIN_RULE_CLAUSES = 3
TITLE_WORDS = 7


def _heading(line: str) -> tuple[str, str] | None:
    """Return (number, rest-of-line) if this line starts a clause."""
    text = line.strip()
    # Ignore things that look like amounts or dates: "1,00,000", "12.06.2026"
    if re.match(r"^\d{1,2}[.,]\d{2,}", text) and not re.match(r"^\d{1,2}\.\d{1,2}\s", text):
        return None
    for pat in (KEYWORD, NUMBERED, LETTERED):
        m = pat.match(text)
        if m:
            return m.group("num"), m.group("rest").strip()
    letters = re.sub(r"[^A-Za-z]", "", text)
    if CAPS.match(text) and len(letters) >= 5 and len(text.split()) <= 8:
        return "", text.rstrip(":").title()
    return None


def _title_from(rest: str, body: str) -> str:
    # "TERMINATION. The tenant ..." or "Security Deposit: The ..." -> use the label part
    m = re.match(r"^([A-Za-z][A-Za-z &/'\-]{2,40})[.:\-]\s", rest)
    if m:
        return m.group(1).strip().title() if m.group(1).isupper() else m.group(1).strip()
    words = (rest or body).split()
    title = " ".join(words[:TITLE_WORDS])
    return title + ("…" if len(words) > TITLE_WORDS else "")


def _heading_only(line: str) -> bool:
    """True if the whole line is a heading ("Clause 4: Rent", "SECURITY DEPOSIT")."""
    text = line.strip()
    return bool(KEYWORD.match(text) or CAPS.match(text)) and len(text.split()) <= 8


def _build(doc: ExtractedDoc, groups: list[tuple[str, str, list[Line]]]) -> list[Clause]:
    clauses: list[Clause] = []
    for i, (num, rest, lines) in enumerate(groups):
        if not lines:
            continue
        start, end = lines[0].start, lines[-1].end
        text = doc.text[start:end]
        if not text.strip():
            continue
        title = _title_from(rest, text) if rest or text else f"Part {i + 1}"
        body_start = 0
        if len(lines) > 1 and _heading_only(lines[0].text):
            body_start = lines[1].start - start
        else:
            # "4. Security Deposit. The tenant ..." -> body starts after the label
            m = re.match(r"^\s*(?:\d{1,2}(?:\.\d{1,2})*[.)]?|\([a-z]{1,4}\))\s+[A-Z][A-Za-z&/'\-]*(?:\s+[A-Za-z&/'\-]+){0,4}[.:]\s+", text)
            if m:
                body_start = m.end()
        clauses.append(Clause(
            id=f"c{len(clauses) + 1}", number=num, title=title, text=text, start=start, end=end,
            body_start=body_start, rects=rects_for_span(doc.lines, start, end),
        ))
    return clauses


def split_by_rules(doc: ExtractedDoc) -> tuple[list[Clause], int]:
    """Returns clauses and how many headings the rules found."""
    groups: list[tuple[str, str, list[Line]]] = [("", "Opening", [])]
    headings = 0
    for line in doc.lines:
        h = _heading(line.text)
        if h:
            headings += 1
            groups.append((h[0], h[1], [line]))
        else:
            groups[-1][2].append(line)
    return _build(doc, groups), headings


def split_by_paragraphs(doc: ExtractedDoc) -> list[Clause]:
    groups: list[tuple[str, str, list[Line]]] = []
    last_block = None
    for line in doc.lines:
        if line.block != last_block:
            groups.append(("", "", []))
            last_block = line.block
        groups[-1][2].append(line)
    return _build(doc, groups)


def split_clauses(doc: ExtractedDoc) -> tuple[list[Clause], str]:
    """Return clauses and the method used: 'rules' or 'paragraphs'."""
    clauses, headings = split_by_rules(doc)
    if headings >= MIN_RULE_CLAUSES:
        return clauses, "rules"
    return split_by_paragraphs(doc), "paragraphs"
