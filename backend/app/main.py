"""TermGuard API. Run with:  python -m uvicorn app.main:app --app-dir backend --port 8000"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import mimetypes
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import storage
from .analyzer import NotSupportedDocument, analyze_pdf
from .checklist import load_checklist
from .config import ROOT, settings
from .extract import ocr_available
from .llm import default_client
from .models import Analysis
from .report import LAWYER, build_report

# Windows sometimes maps .js to text/plain in the registry, which stops the page loading.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

# Log ids and counts only. Document text is never logged.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("termguard")
SAMPLES = ROOT / "samples" / "public"
DIST = ROOT / "frontend" / "dist"


async def _sweeper() -> None:
    while True:
        removed = await run_in_threadpool(storage.sweep)
        if removed:
            log.info("auto-deleted %d expired document(s)", removed)
        await asyncio.sleep(60)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_sweeper())
    yield
    task.cancel()


app = FastAPI(title="TermGuard", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "llm_enabled": settings.llm_enabled, "llm_model": settings.llm_model if settings.llm_enabled else None,
            "ocr_available": ocr_available(), "retention_minutes": settings.retention_minutes}


def _run(data: bytes, filename: str) -> Analysis:
    doc_id = uuid.uuid4().hex[:12]
    try:
        analysis = analyze_pdf(data, filename, client=default_client(), doc_id=doc_id)
    except NotSupportedDocument as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("analysis failed for %s", doc_id)
        raise HTTPException(status_code=400, detail="This PDF could not be read. Try another copy of the file.") from exc
    storage.save(analysis, data)
    log.info("analysed %s: %d clauses, %d findings, %d dropped by quote check", doc_id,
             len(analysis.clauses), len(analysis.findings), analysis.dropped_unverified)
    return analysis


@app.post("/api/documents", response_model=Analysis)
async def upload(file: UploadFile = File(...)) -> Analysis:
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"The file is larger than {settings.max_upload_mb} MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Please upload a PDF file.")
    return await run_in_threadpool(_run, data, Path(file.filename or "document.pdf").name)


@app.get("/api/samples")
def samples() -> list[dict]:
    out = []
    for f in sorted(SAMPLES.glob("*.pdf")):
        kind = "Offer letter" if "offer" in f.stem else "Rental agreement"
        out.append({"name": f.name, "kind": kind, "title": f.stem.replace("_", " ").replace("-", " ").title()})
    return out


@app.post("/api/samples/{name}", response_model=Analysis)
async def analyze_sample(name: str) -> Analysis:
    path = (SAMPLES / name).resolve()
    if path.parent != SAMPLES.resolve() or not path.exists():
        raise HTTPException(404, "Sample not found.")
    return await run_in_threadpool(_run, path.read_bytes(), path.name)


@app.get("/api/documents/{doc_id}", response_model=Analysis)
def get_document(doc_id: str) -> Analysis:
    analysis = storage.load(doc_id)
    if not analysis:
        raise HTTPException(404, "This document was deleted or has expired.")
    return analysis


@app.get("/api/documents/{doc_id}/file")
def get_file(doc_id: str) -> FileResponse:
    if not storage.load(doc_id) or not storage.pdf_path(doc_id).exists():
        raise HTTPException(404, "This document was deleted or has expired.")
    return FileResponse(storage.pdf_path(doc_id), media_type="application/pdf")


@app.get("/api/documents/{doc_id}/report.pdf")
def get_report(doc_id: str) -> Response:
    analysis = storage.load(doc_id)
    if not analysis:
        raise HTTPException(404, "This document was deleted or has expired.")
    stem = Path(analysis.filename).stem
    return Response(build_report(analysis), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="termguard-{stem}.pdf"'})


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    removed = storage.delete(doc_id)
    log.info("deleted %s on request", doc_id)
    return {"deleted": removed}


@app.get("/api/checklist/{doc_type}")
def checklist(doc_type: str) -> dict:
    if doc_type not in ("rental", "offer_letter"):
        raise HTTPException(404, "Unknown document type.")
    c = load_checklist(doc_type)  # type: ignore[arg-type]
    return {"title": c.title, "disclaimer": c.disclaimer, "lawyer": LAWYER[doc_type],
            "items": [i.model_dump(exclude={"triggers", "escalate", "soften"}) for i in c.items],
            "expected": [e.model_dump(exclude={"present"}) for e in c.expected]}


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        target = (DIST / path).resolve()
        if path and target.is_file() and DIST.resolve() in target.parents:
            return FileResponse(target)
        return FileResponse(DIST / "index.html")
