"""Phase 3: load the YAML knowledge base."""
from __future__ import annotations

import re
from functools import lru_cache

import yaml

from .config import BACKEND
from .models import Checklist, DocType

FILES: dict[str, str] = {"rental": "rental.yaml", "offer_letter": "offer_letter.yaml"}


@lru_cache(maxsize=4)
def load_checklist(doc_type: DocType) -> Checklist:
    if doc_type not in FILES:
        raise ValueError(f"No checklist for {doc_type}")
    path = BACKEND / "knowledge" / FILES[doc_type]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    checklist = Checklist(**data)
    # Fail early if a pattern in the YAML is broken.
    for item in checklist.items:
        for pat in item.triggers + item.escalate + item.soften:
            re.compile(pat, re.I)
    for exp in checklist.expected:
        for pat in exp.present:
            re.compile(pat, re.I)
    return checklist
