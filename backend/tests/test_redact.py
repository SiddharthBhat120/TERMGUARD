from app.redact import Redactor


def test_redacts_personal_details_and_restores():
    text = ("Agreement between Mr. Ramesh Kulkarni, S/o Shri Venkatesh Kulkarni, residing at #42, 3rd Cross, "
            "Jayanagar, Bengaluru 560011 and Ms. Priya Nair (priya.nair@example.com, +91 98450 12345). "
            "PAN ABCDE1234F, Aadhaar 2345 6789 0123, account 123456789012345. Rent is Rs. 18,000.")
    r = Redactor()
    out = r.redact(text)
    for secret in ["Ramesh Kulkarni", "Venkatesh Kulkarni", "Jayanagar", "Priya Nair", "priya.nair@example.com",
                   "98450 12345", "ABCDE1234F", "2345 6789 0123", "123456789012345"]:
        assert secret not in out, secret
    assert "Rs. 18,000" in out  # amounts stay, they are needed for the analysis
    assert "Mr. [PERSON_" in out
    assert r.restore(out) == text


def test_same_person_gets_same_placeholder():
    r = Redactor()
    a = r.redact("Mr. Arjun Menon signs here.")
    b = r.redact("Witnessed for Arjun Menon.")
    ph = a.split("Mr. ")[1].split()[0]
    assert ph in b
