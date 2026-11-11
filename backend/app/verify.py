"""The quote check: every finding must point at text that really exists in the clause.

Why this stops made-up findings: a language model can write a convincing explanation for a
clause that does not exist. If we demand a verbatim quote and then search for it in the real
document text, a finding can only survive if the words are on the page. Anything invented,
paraphrased or copied from another document fails the search and is dropped before the user
ever sees it.
"""
from __future__ import annotations

import re

QUOTE_CHARS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", " ": " "})


def _norm_with_map(text: str) -> tuple[str, list[int]]:
    """Lower-case, unify quote marks, and squash whitespace.

    Returns the normalised string and, for each of its characters, the index in the original.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = True
    for i, ch in enumerate(text.translate(QUOTE_CHARS)):
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
        else:
            out.append(ch.lower())
            idx.append(i)
            prev_space = False
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


ABBR_DOT = re.compile(r"\b(Rs|No|Mr|Mrs|Ms|Dr|Smt|Shri|Sri|St|Pvt|Ltd|Co|Nos|Sq|Ft|viz|approx)\.", re.I)


def match_text(text: str) -> str:
    """Same-length copy of the text for pattern matching.

    Line breaks become spaces (wrapped lines are one sentence) and the dot in abbreviations
    like "Rs." becomes a space, so patterns written as "[^.]" do not stop at "Rs. 15,000".
    Offsets stay identical to the original text.
    """
    return ABBR_DOT.sub(lambda m: m.group(1) + " ", text.replace("\n", " "))


def find_quote(haystack: str, quote: str) -> tuple[int, int] | None:
    """Return (start, end) of `quote` inside `haystack`, ignoring case and spacing.

    Small differences in whitespace, line breaks and curly quotes are allowed. Any change in
    the words themselves is not. Leading/trailing ellipses and punctuation are trimmed.
    """
    q = quote.translate(QUOTE_CHARS).strip().strip('"').strip("'").strip()
    q = re.sub(r"^(\.\.\.|…)\s*|\s*(\.\.\.|…)$", "", q).strip().rstrip(".;,")
    if len(q) < 4:
        return None
    hay_n, hay_map = _norm_with_map(haystack)
    q_n, _ = _norm_with_map(q)
    pos = hay_n.find(q_n)
    if pos < 0:
        return None
    start = hay_map[pos]
    end = hay_map[pos + len(q_n) - 1] + 1
    return start, end


ABBREV = {"rs", "no", "mr", "mrs", "ms", "dr", "shri", "smt", "sri", "st", "i.e", "e.g", "etc", "pvt", "ltd", "co", "inr", "approx", "sq", "ft", "nos", "viz"}


def _is_boundary(text: str, i: int) -> bool:
    """Is text[i] the end of a sentence?"""
    ch = text[i]
    if ch == ";":
        return True
    if ch != ".":
        return False
    nxt = text[i + 1] if i + 1 < len(text) else " "
    if not nxt.isspace():
        return False  # 1.5, i.e.
    m = re.search(r"([A-Za-z.]+)$", text[max(0, i - 8):i])
    if m and m.group(1).lower().strip(".") in ABBREV:
        return False
    # "4." at the very start of a line is a clause number, not a sentence end
    line_start = text.rfind("\n", 0, i) + 1
    if re.fullmatch(r"\s*\d{1,2}(\.\d{1,2})*", text[line_start:i]):
        return False
    return True


def sentence_around(text: str, start: int, end: int, max_len: int = 360) -> tuple[int, int]:
    """Expand a match to the sentence that contains it (used by the rule engine for quotes)."""
    left = start
    while left > 0 and not _is_boundary(text, left - 1) and start - left < max_len:
        left -= 1
    right = end
    while right < len(text) and not _is_boundary(text, right) and right - end < max_len:
        right += 1
    if right < len(text):
        right += 1
    while left < right and text[left].isspace():
        left += 1
    # Skip a clause number like "4." or "(b)" at the start of the sentence.
    m = re.match(r"^(\d{1,2}(\.\d{1,2})*[.)]?|\([a-z]{1,4}\))\s+", text[left:right])
    if m:
        left += m.end()
    return left, right
