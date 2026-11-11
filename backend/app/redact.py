"""Phase 7: hide personal details before any text leaves the server.

Regex rules catch emails, phone numbers, Aadhaar/PAN/bank numbers, names after
honorifics (Mr., Smt., Shri ...), "S/o" relations and addresses. If spaCy with an
English model is installed, its PERSON entities are redacted too (optional).
The placeholder map stays on the server and is used to restore the original words
only for display.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NAME = r"[A-Z][a-zA-Z]+(?:\s+[A-Z]\.?)*(?:\s+[A-Z][a-zA-Z]+){0,3}"
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("AADHAAR", re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("PHONE", re.compile(r"(?:\+91[\s-]?|\b0)?\b[6-9]\d{4}[\s-]?\d{5}\b")),
    ("PHONE", re.compile(r"\b0\d{2,4}[\s-]\d{6,8}\b")),
    ("ACCOUNT", re.compile(r"\b\d{9,18}\b")),
    ("ADDRESS", re.compile(
        r"(?:(?:Flat|House|Door|Plot|Apartment|Apt|Room|Shop)\s*(?:No\.?|Number)?\s*[:#]?\s*[\w/-]+|#\s*\d+[\w/-]*)"
        r"[^\n]{0,140}?(?:\b\d{3}\s?\d{3}\b|$)", re.M)),
    ("ADDRESS", re.compile(r"residing at (?P<v>[^\n(]{5,160}?)(?=\s*\(|\s*,?\s*hereinafter|\.\s|$)", re.M | re.I)),
    # Only the named group "v" is replaced; the honorific stays readable.
    ("PERSON", re.compile(rf"\b(?:Mr|Ms|Mrs|Dr|Smt|Sri|Shri|Kumari|Miss)\.?\s+(?P<v>{NAME})")),
    ("PERSON", re.compile(rf"\b[SDW]/[Oo]\.?\s+(?:(?:Shri|Sri|Mr)\.?\s+)?(?P<v>{NAME})")),
    ("PERSON", re.compile(rf"\bDear\s+(?P<v>{NAME})(?=\s*,)")),
    ("PERSON", re.compile(rf"\bName\s*:\s*(?P<v>{NAME})")),
]
PLACEHOLDER = re.compile(r"\[(?:EMAIL|AADHAAR|PAN|IFSC|PHONE|ACCOUNT|ADDRESS|PERSON|ORG)_\d+\]")


@dataclass
class Redactor:
    mapping: dict[str, str] = field(default_factory=dict)  # placeholder -> original
    reverse: dict[str, str] = field(default_factory=dict)  # original -> placeholder
    counts: dict[str, int] = field(default_factory=dict)

    def _placeholder(self, kind: str, original: str) -> str:
        if original in self.reverse:
            return self.reverse[original]
        self.counts[kind] = self.counts.get(kind, 0) + 1
        ph = f"[{kind}_{self.counts[kind]}]"
        self.mapping[ph] = original
        self.reverse[original] = ph
        return ph

    def redact(self, text: str) -> str:
        # Known originals first, so the same person gets the same placeholder everywhere.
        for original in sorted(self.reverse, key=len, reverse=True):
            text = text.replace(original, self.reverse[original])
        for kind, pat in PATTERNS:
            def repl(m: re.Match[str], kind: str = kind) -> str:
                group = "v" if "v" in m.re.groupindex else 0
                value = (m.group(group) or "").strip().rstrip(",.")
                if not value or PLACEHOLDER.fullmatch(value) or "[" in value:
                    return m.group(0)
                return m.group(0).replace(value, self._placeholder(kind, value), 1)
            text = pat.sub(repl, text)
        text = self._ner(text)
        return text

    def _ner(self, text: str) -> str:  # pragma: no cover - optional dependency
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            return text
        for ent in reversed(list(nlp(text).ents)):
            if ent.label_ == "PERSON" and "[" not in ent.text and len(ent.text) > 3:
                text = text[: ent.start_char] + self._placeholder("PERSON", ent.text) + text[ent.end_char:]
        return text

    def restore(self, text: str) -> str:
        return PLACEHOLDER.sub(lambda m: self.mapping.get(m.group(0), m.group(0)), text)

    @property
    def total(self) -> int:
        return len(self.mapping)
