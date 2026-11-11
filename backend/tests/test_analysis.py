"""Phase 4 tests, including the quote check against made-up LLM output."""
import json

from app.analyzer import analyze_pdf
from app.verify import find_quote


class FakeLLM:
    """Pretends to be the model. Returns whatever JSON we give it and records prompts."""

    def __init__(self, make_reply):
        self.make_reply = make_reply
        self.prompts: list[str] = []

    def complete(self, system: str, user: str) -> str:
        self.prompts.append(user)
        return self.make_reply(system, user)


def test_find_quote_tolerates_spacing_but_not_rewording():
    clause = "The Owner may forfeit the\ndeposit at his sole   discretion."
    assert find_quote(clause, "the owner may forfeit the deposit at his sole discretion")
    assert find_quote(clause, "“The Owner may forfeit the deposit”")
    assert find_quote(clause, "The Owner can keep the deposit whenever he wants") is None
    assert find_quote(clause, "may") is None  # too short to prove anything


def test_rule_engine_flags_known_red_flags(fixture_bytes):
    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf")
    ids = {f.checklist_id for f in a.findings}
    assert {"R02_deposit_forfeit", "R04_lock_in", "R06_eviction", "R08_repairs_on_tenant"} <= ids
    assert a.engine == "rules" and a.dropped_unverified == 0
    for f in a.findings:
        assert f.rects, "every finding must be highlightable"
        assert f.quote and find_quote(" ".join(c.text for c in a.clauses), f.quote)
        assert f.explanation_hi and f.explanation_kn


def test_llm_fake_quote_is_rejected(fixture_bytes):
    def reply(system, user):
        if "Translate" in system:
            return json.dumps({"items": []})
        results = []
        for block in user.split("CLAUSE ")[1:]:
            cid = block.split()[0]
            if "forfeit" in block:
                results.append({"clause_id": cid, "findings": [
                    {"checklist_id": "R02_deposit_forfeit", "risk": "high",
                     "explanation": "The owner can keep your deposit. Ask for clear reasons.",
                     "quote": "The Owner may forfeit the deposit at his sole discretion",
                     "question": "When exactly can you keep the deposit?"},
                    {"checklist_id": "R01_deposit_high", "risk": "high",
                     "explanation": "This is invented text that is not in the clause at all.",
                     "quote": "The tenant must pay twenty months of rent as deposit",
                     "question": "Is this real?"},
                ]})
        return json.dumps({"results": results})

    llm = FakeLLM(reply)
    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf", client=llm)
    assert a.engine == "llm"
    kept = [(f.checklist_id, f.source) for f in a.findings]
    assert ("R02_deposit_forfeit", "llm") in kept
    assert not any("twenty months" in f.quote for f in a.findings)
    assert a.dropped_unverified == 1


def test_llm_cannot_use_items_that_were_not_candidates(fixture_bytes):
    def reply(system, user):
        cid = user.split("CLAUSE ")[1].split()[0]
        return json.dumps({"results": [{"clause_id": cid, "findings": [{
            "checklist_id": "O02_bond", "risk": "high", "explanation": "Wrong checklist entirely for this file.",
            "quote": user.split('"""')[1][:30], "question": "Why?"}]}]})

    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf", client=FakeLLM(reply))
    assert not any(f.checklist_id == "O02_bond" for f in a.findings)


def test_bad_llm_json_falls_back_to_rules(fixture_bytes):
    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf",
                    client=FakeLLM(lambda s, u: "sorry, I cannot help with that"))
    assert a.engine == "rules"
    assert any(f.checklist_id == "R06_eviction" for f in a.findings)


def test_llm_only_sees_redacted_text(fixture_bytes):
    llm = FakeLLM(lambda s, u: json.dumps({"results": []}))
    analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf", client=llm)
    sent = "\n".join(llm.prompts)
    assert "Ramesh Kulkarni" not in sent and "98450 12345" not in sent and "Jayanagar" not in sent
