from app.analyzer import analyze_pdf


def facts(a):
    return {f.key: f.value for f in a.facts}


def test_rental_facts_are_shown_as_written(fixture_bytes):
    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf")
    f = facts(a)
    assert f["rent"] == "Rs. 18,000/-"
    assert f["lock_in"] == "11 months"
    assert f["notice"] == "three months"
    for fact in a.facts:
        assert fact.value.replace(" ", "") in fact.quote.replace(" ", "")
        assert fact.rects


def test_offer_facts_no_calculations(fixture_bytes):
    f = facts(analyze_pdf(fixture_bytes("offer_startup_bond.pdf"), "x.pdf"))
    assert f["ctc"] == "Rs. 6,00,000 per annum"
    assert f["fixed"] == "Rs. 4,20,000 per annum"
    assert f["variable"] == "Rs. 1,80,000 per annum"
    assert f["notice"] == "90 days"
    # No derived numbers such as a monthly figure (50,000) appear anywhere.
    assert not any("50,000" in v for v in f.values())


def test_missing_items(fixture_bytes):
    a = analyze_pdf(fixture_bytes("rental_bengaluru_strict.pdf"), "x.pdf")
    missing = {m.id for m in a.missing}
    assert "E_R01_deposit_return" in missing   # no refund timeline anywhere
    assert "E_R02_notice" not in missing       # notice is mentioned
