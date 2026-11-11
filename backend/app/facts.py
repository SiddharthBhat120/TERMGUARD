"""Phase 5: key facts for the summary card, and expected items that are missing.

Values are shown exactly as written in the document. We do no maths the document does not
do (for example we never turn "Rs. 6,00,000 per annum" into a monthly figure).
"""
from __future__ import annotations

import re

from .extract import rects_for_span
from .models import Checklist, DocType, ExtractedDoc, KeyFact, MissingItem
from .verify import find_quote, match_text, sentence_around

AMOUNT = r"(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?\s*(?:/-)?(?:\s*(?:lakhs?|lacs?|LPA|crores?))?(?:\s*(?:per|/|a)\s*(?:month|annum|year|p\.?a\.?|p\.?m\.?))?"
NUMWORD = r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|thirty|sixty|ninety)"
PERIOD = rf"{NUMWORD}\s*(?:\(\w+\)\s*)?(?:calendar\s*)?(?:months?|days?|years?)"

FACTS: dict[str, list[tuple[str, str, list[str]]]] = {
    "rental": [
        ("rent", "Monthly rent", [rf"(?:monthly rent|rent|licen[cs]e fee)[^.\n]{{0,70}}?({AMOUNT})"]),
        ("deposit", "Security deposit", [
            rf"(?:security deposit|deposit|advance)[^.]{{0,90}}?({AMOUNT})",
            rf"({AMOUNT})[^.]{{0,60}}?as\s*(?:a\s*)?(?:refundable\s*)?(?:security\s*)?deposit",
            rf"(?:security deposit|deposit)[^.]{{0,90}}?({NUMWORD}\s*(?:\(\w+\)\s*)?months?\W{{0,2}}s?\s*rent)",
        ]),
        ("term", "Agreement period", [rf"(?:period|term)\s*of\s*({PERIOD})"]),
        ("lock_in", "Lock-in period", [rf"lock[- ]?in\s*(?:period)?\s*(?:of|is|:|for|shall be|will be)\s*({PERIOD})"]),
        ("notice", "Notice period", [
            rf"({PERIOD})\W{{0,2}}s?\s*(?:prior\s*|advance\s*|written\s*)*notice",
            rf"notice\s*(?:period\s*)?of\s*(?:not less than\s*|at least\s*)?({PERIOD})",
        ]),
    ],
    "offer_letter": [
        ("ctc", "Total CTC", [rf"(?:CTC|cost to (?:the )?company|total (?:annual )?compensation)[^.]{{0,90}}?({AMOUNT})"]),
        ("fixed", "Fixed pay", [
            rf"({AMOUNT})\s*(?:is|as|towards)\s*(?:the\s*|a\s*)?fixed",
            rf"fixed\s*(?:pay|salary|component|compensation)\s*(?:of|is|:|amounting to|will be)?\s*({AMOUNT})",
        ]),
        ("variable", "Variable pay", [
            rf"({AMOUNT})\s*(?:is|as|towards)\s*(?:the\s*|a\s*)?(?:variable|performance[- ](?:linked|based))",
            rf"variable\s*(?:pay|component|bonus|compensation|incentive)\s*(?:of|is|:|amounting to|will be)?\s*({AMOUNT})",
            r"variable\s*(?:pay|component|bonus)[^.]{0,60}?(\d{1,2}\s*%)",
        ]),
        ("bond", "Bond or service period", [
            rf"(?:bond|service agreement|minimum service)[^.]{{0,120}}?({AMOUNT})",
            rf"(?:bond|minimum (?:service|period))[^.]{{0,80}}?({PERIOD})",
            rf"serve\s*(?:the company\s*)?(?:for\s*)?(?:a\s*)?minimum\s*(?:period\s*)?of\s*({PERIOD})",
        ]),
        ("notice", "Notice period", [
            rf"notice\s*period[^.]{{0,40}}?({PERIOD})",
            rf"({PERIOD})\W{{0,2}}s?\s*(?:prior\s*|advance\s*|written\s*)*notice",
        ]),
        ("joining", "Joining date", [r"(?:date of joining|joining date|join (?:us )?on)\s*(?:is|will be|:)?\s*([0-9]{1,2}(?:st|nd|rd|th)?[\s/.-]*(?:[A-Za-z]+|\d{1,2})[\s/.,-]*\d{2,4})"]),
    ],
}


# The sentence around a fact must also match this (e.g. a notice period must be about leaving,
# not about a rent increase).
REQUIRE = {"notice": r"vacat|leav|terminat|quit|\bend\b|exit|resign|either (party|side)|\bgive\b|\bserve\b|notice period"}


def extract_facts(doc: ExtractedDoc, doc_type: DocType) -> list[KeyFact]:
    text = doc.text
    flat = match_text(text)
    facts: list[KeyFact] = []
    for key, label, patterns in FACTS.get(doc_type, []):
        found = None
        for pat in patterns:
            for m in re.finditer(pat, flat, re.I):
                s, e = sentence_around(text, m.start(), m.end())
                if key in REQUIRE and not re.search(REQUIRE[key], flat[s:e], re.I):
                    continue
                found = (m, s, e)
                break
            if found:
                break
        if found:
            m, s, e = found
            value = " ".join(text[m.start(1):m.end(1)].split()).rstrip(",")  # original characters
            quote = " ".join(text[s:e].split())
            # Same verification step as findings: both the value and the quote must be on the page.
            span = find_quote(text, quote)
            if span and find_quote(quote, value):
                facts.append(KeyFact(key=key, label=label, value=value, quote=quote,
                                     rects=rects_for_span(doc.lines, span[0], span[1])))
    return facts


def find_missing(text: str, checklist: Checklist) -> list[MissingItem]:
    flat = match_text(text)
    out: list[MissingItem] = []
    for exp in checklist.expected:
        if not any(re.search(p, flat, re.I) for p in exp.present):
            out.append(MissingItem(id=exp.id, name=exp.name, why=exp.why, question=exp.question))
    return out


def flesch_reading_ease(text: str) -> float:
    """Higher is easier. 60-70 is plain English; above 70 is easy."""
    sentences = max(1, len(re.findall(r"[.!?]+(\s|$)", text)))
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    syllables = 0
    for w in words:
        groups = re.findall(r"[aeiouy]+", w.lower())
        count = len(groups)
        if w.lower().endswith("e") and count > 1:
            count -= 1
        syllables += max(1, count)
    return round(206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words)), 1)
