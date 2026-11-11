"""SQLite storage for analyses, plus auto-deletion of uploaded files.

Only the analysis JSON (which contains clause text needed for the viewer) and the PDF are
stored, and both are deleted when the retention time ends or the user presses "Delete now".
"""
from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .config import settings
from .models import Analysis


def _conn() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS documents ("
        " id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at REAL NOT NULL,"
        " expires_at REAL NOT NULL, analysis TEXT NOT NULL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON documents(expires_at)")
    return conn


def pdf_path(doc_id: str) -> Path:
    return settings.uploads_dir / f"{doc_id}.pdf"


def save(analysis: Analysis, pdf: bytes) -> None:
    with closing(_conn()) as conn, conn:
        pdf_path(analysis.id).write_bytes(pdf)
        conn.execute(
            "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?)",
            (analysis.id, analysis.filename, analysis.created_at, analysis.expires_at, analysis.model_dump_json()),
        )


def load(doc_id: str) -> Analysis | None:
    with closing(_conn()) as conn:
        row = conn.execute("SELECT analysis, expires_at FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not row or row[1] < time.time():
        return None
    return Analysis.model_validate_json(row[0])


def delete(doc_id: str) -> bool:
    with closing(_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    path = pdf_path(doc_id)
    existed = path.exists()
    path.unlink(missing_ok=True)
    return cur.rowcount > 0 or existed


def sweep() -> int:
    """Delete everything past its retention time. Returns how many documents were removed."""
    now = time.time()
    with closing(_conn()) as conn, conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM documents WHERE expires_at < ?", (now,))]
        conn.execute("DELETE FROM documents WHERE expires_at < ?", (now,))
    for doc_id in ids:
        pdf_path(doc_id).unlink(missing_ok=True)
    # Orphan files (e.g. after a crash) older than the retention time.
    for f in settings.uploads_dir.glob("*.pdf"):
        if f.stat().st_mtime < now - settings.retention_minutes * 60:
            f.unlink(missing_ok=True)
    return len(ids)
