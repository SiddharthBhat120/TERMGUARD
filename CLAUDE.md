# TermGuard

Users upload a rental agreement or job offer letter (PDF). The app extracts clauses, flags risky ones
against a YAML checklist, and explains them in plain language with the exact source text cited.
It gives information, not legal advice.

## Stack
FastAPI, PyMuPDF, Tesseract (optional), TF-IDF matcher (sentence-transformers optional), optional
OpenAI-compatible LLM client (httpx), SQLite, ReportLab; React 19 + Vite + PDF.js.

## Rules
- Type hints everywhere; tests with pytest (`python -m pytest backend/tests -q`).
- LLM output is JSON validated with Pydantic; any failure falls back to the rule engine.
- Every finding and key fact must carry a verbatim quote and page positions, and must pass
  `verify.find_quote` against the clause text. Never bypass this check.
- Pattern matching runs on `verify.match_text(text)` (same length, safe for "Rs." and line breaks).
- Redact with `redact.Redactor` before any text leaves the server. Never log document text.
- Show amounts as written. Do no calculations the document does not support.
- No real documents in git. Private samples go in `samples/private/` (ignored).

## Layout
backend/app (pipeline), backend/knowledge (checklists), backend/tests, frontend (dist is committed),
samples (synthetic docs + generator), eval (labelling, metrics, results.md), docs.
