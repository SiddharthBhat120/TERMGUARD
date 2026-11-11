import re

import pytest

from app.checklist import load_checklist
from app.verify import match_text


@pytest.mark.parametrize("doc_type", ["rental", "offer_letter"])
def test_checklist_is_complete(doc_type):
    c = load_checklist(doc_type)
    ids = [i.id for i in c.items] + [e.id for e in c.expected]
    assert len(ids) == len(set(ids))
    assert len(c.items) >= 8 and len(c.expected) >= 5
    assert "not legal advice" in c.disclaimer
    for item in c.items:
        assert item.triggers, item.id
        assert item.explanation_hi and item.explanation_kn, f"missing translation for {item.id}"
        assert re.search(r"[ऀ-ॿ]", item.explanation_hi), "Hindi should be in Devanagari"
        assert re.search(r"[ಀ-೿]", item.explanation_kn), "Kannada should be in Kannada script"
        assert item.question.endswith("?")
        # The example wording should trigger its own item: a cheap self-check of the patterns.
        assert any(re.search(p, match_text(item.example), re.I) for p in item.triggers), item.id
