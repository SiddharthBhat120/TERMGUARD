from app.clauses import split_clauses
from app.extract import extract_pdf
from tests.helpers import doc_from_lines


def titles(clauses):
    return [c.title for c in clauses]


def test_numbered_with_inline_titles():
    doc = doc_from_lines([
        "RENT AGREEMENT between the owner and the tenant",
        "1. Rent. The tenant pays Rs. 10,000 per month.",
        "2. Security Deposit. The tenant pays Rs. 20,000.",
        "2.1 The deposit is refunded within 30 days.",
        "3. Notice. One month notice applies.",
    ])
    clauses, method = split_clauses(doc)
    assert method == "rules"
    assert [c.number for c in clauses][-4:] == ["1", "2", "2.1", "3"]
    assert "Security Deposit" in titles(clauses)
    rent = next(c for c in clauses if c.number == "1")
    assert rent.text[rent.body_start:].startswith("The tenant pays")


def test_clause_keyword_and_caps_headings():
    doc = doc_from_lines([
        "Clause 1: Licence fee", "The fee is Rs. 30,000 per month.",
        "Clause 2 - Deposit", "Refundable deposit of Rs. 1,00,000.",
        "TERMINATION", "Either party may end this with one month's notice.",
    ])
    clauses, method = split_clauses(doc)
    assert method == "rules"
    assert len(clauses) == 3
    assert clauses[2].title == "Termination"
    assert clauses[0].text[clauses[0].body_start:].startswith("The fee")


def test_lettered_subclauses():
    doc = doc_from_lines([
        "1. Tenant duties. The tenant shall:",
        "(a) pay rent on time;", "(b) keep the flat clean;", "(c) not sublet the flat.",
    ])
    clauses, _ = split_clauses(doc)
    assert [c.number for c in clauses] == ["1", "a", "b", "c"]


def test_amounts_and_dates_are_not_headings():
    doc = doc_from_lines(["1. Rent. Pay", "1,00,000 rupees on", "12.06.2026 and", "2. Notice. One month.", "3. End. Done."])
    clauses, _ = split_clauses(doc)
    assert [c.number for c in clauses] == ["1", "2", "3"]


def test_unnumbered_document_falls_back_to_paragraphs(fixture_bytes):
    clauses, method = split_clauses(extract_pdf(fixture_bytes("rental_plain_letter_style.pdf")))
    assert method == "paragraphs"
    assert len(clauses) >= 6
    assert all(c.rects for c in clauses)
