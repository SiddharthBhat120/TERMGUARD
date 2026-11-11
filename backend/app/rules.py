"""Offline rule engine: decides which checklist items apply to a clause using the
patterns written in the YAML checklist. Used when no LLM key is set, and as a
candidate generator for the LLM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ChecklistItem, Clause, Risk
from .verify import match_text, sentence_around

LEVELS: list[Risk] = ["low", "medium", "high"]
MIN_QUOTE_WORDS = 5


@dataclass
class RuleHit:
    item: ChecklistItem
    risk: Risk
    start: int  # offsets inside clause.text
    end: int


def raise_risk(base: Risk, steps: int) -> Risk:
    return LEVELS[min(len(LEVELS) - 1, LEVELS.index(base) + steps)]


def _best_sentence(item: ChecklistItem, text: str, flat: str, body: int) -> tuple[int, int] | None:
    """First sentence in the clause body that triggers the item (and passes `require`)."""
    fallback = None
    for pat in item.triggers:
        for m in re.finditer(pat, flat, re.I):
            if m.end() <= body:  # the match is only in the heading
                continue
            s, e = sentence_around(text, max(m.start(), body), m.end())
            s = max(s, body)
            sentence = flat[s:e]
            if item.require and not any(re.search(p, sentence, re.I) for p in item.require):
                continue
            if len(sentence.split()) >= MIN_QUOTE_WORDS:
                return s, e
            fallback = fallback or (s, e)
    return fallback


def rule_hits(clause: Clause, items: list[ChecklistItem]) -> list[RuleHit]:
    text = clause.text
    flat = match_text(text)  # same length; safe for "[^.]" patterns
    hits: list[RuleHit] = []
    for item in items:
        if any(re.search(p, flat, re.I) for p in item.soften):
            continue
        span = _best_sentence(item, text, flat, clause.body_start)
        if not span:
            continue
        s, e = span
        steps = sum(1 for p in item.escalate if re.search(p, flat[s:e], re.I))
        hits.append(RuleHit(item=item, risk=raise_risk(item.risk, steps), start=s, end=e))
    return hits
