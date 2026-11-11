"""Decide whether a document is a rental agreement, an offer letter, or something else."""
from __future__ import annotations

import re

from .models import DocType

RENTAL_WORDS = {
    r"\blandlord\b": 3, r"\btenant\b": 3, r"\blessor\b": 3, r"\blessee\b": 3,
    r"\blicensor\b": 3, r"\blicensee\b": 3, r"leave and licen[cs]e": 4,
    r"rent(al)? agreement": 4, r"\bpremises\b": 2, r"security deposit": 2,
    r"monthly rent": 3, r"\btenancy\b": 3, r"\bflat\b": 1, r"\brent\b": 1, r"\bowner\b": 1,
    r"paying guest|\bpg\b": 3, r"\bvacat": 2, r"\baccommodation\b": 2, r"\bhouse\b": 1,
}
OFFER_WORDS = {
    r"offer (letter|of employment)": 4, r"\bctc\b": 3, r"cost to company": 3,
    r"\bdesignation\b": 2, r"date of joining": 3, r"\bjoining\b": 2,
    r"\bemployment\b": 2, r"\bprobation\b": 2, r"\bsalary\b": 2,
    r"\bcompensation\b": 2, r"\bemployee\b": 2, r"human resources|\bhr\b": 1,
}
LABELS: dict[DocType, str] = {
    "rental": "Rental agreement",
    "offer_letter": "Job offer letter",
    "other": "Other document",
}
MIN_SCORE = 6


def _score(text: str, table: dict[str, int]) -> int:
    return sum(min(len(re.findall(p, text)), 3) * w for p, w in table.items())


def detect_doc_type(text: str) -> tuple[DocType, dict[str, int]]:
    lower = text.lower()
    scores = {"rental": _score(lower, RENTAL_WORDS), "offer_letter": _score(lower, OFFER_WORDS)}
    best: DocType = "rental" if scores["rental"] >= scores["offer_letter"] else "offer_letter"
    if scores[best] < MIN_SCORE:
        return "other", scores
    return best, scores
