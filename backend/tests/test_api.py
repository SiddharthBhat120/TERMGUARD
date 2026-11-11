from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["llm_enabled"] is False


def test_upload_view_report_delete(fixture_bytes):
    r = client.post("/api/documents", files={"file": ("offer.pdf", fixture_bytes("offer_startup_bond.pdf"), "application/pdf")})
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["doc_type"] == "offer_letter" and a["findings"]
    doc_id = a["id"]
    assert client.get(f"/api/documents/{doc_id}").status_code == 200
    pdf = client.get(f"/api/documents/{doc_id}/file")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    rep = client.get(f"/api/documents/{doc_id}/report.pdf")
    assert rep.status_code == 200 and rep.content.startswith(b"%PDF")
    assert client.delete(f"/api/documents/{doc_id}").json()["deleted"] is True
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
    assert client.get(f"/api/documents/{doc_id}/file").status_code == 404


def test_rejects_other_documents_politely(fixture_bytes):
    r = client.post("/api/documents", files={"file": ("n.pdf", fixture_bytes("other_document.pdf"), "application/pdf")})
    assert r.status_code == 422
    assert "rental agreements and job offer letters" in r.json()["detail"]


def test_rejects_non_pdf():
    r = client.post("/api/documents", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_samples_and_checklist():
    names = [s["name"] for s in client.get("/api/samples").json()]
    assert "rental_bengaluru_strict.pdf" in names
    assert client.post("/api/samples/../../secret.pdf").status_code in (404, 405)
    c = client.get("/api/checklist/rental").json()
    assert c["lawyer"] and "triggers" not in c["items"][0]


def test_expired_documents_are_swept(fixture_bytes):
    import time

    from app import storage
    r = client.post("/api/documents", files={"file": ("r.pdf", fixture_bytes("rental_bengaluru_strict.pdf"), "application/pdf")})
    doc_id = r.json()["id"]
    a = storage.load(doc_id)
    a.expires_at = time.time() - 1
    storage.save(a, fixture_bytes("rental_bengaluru_strict.pdf"))
    assert storage.sweep() >= 1
    assert not storage.pdf_path(doc_id).exists()
