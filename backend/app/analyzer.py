"""The full pipeline: PDF -> clauses -> findings (verified) -> missing items -> key facts."""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

from . import llm as llm_mod
from .checklist import load_checklist
from .clauses import split_clauses
from .config import settings
from .doctype import LABELS, detect_doc_type
from .extract import extract_pdf, rects_for_span
from .facts import extract_facts, find_missing
from .matcher import make_matcher
from .models import Analysis, Checklist, ChecklistItem, Clause, ExtractedDoc, Finding, LLMFinding
from .redact import Redactor
from .rules import rule_hits
from .verify import find_quote

log = logging.getLogger("termguard.analyzer")
MIN_CLAUSE_CHARS = 40
LLM_BATCH = 6


class NotSupportedDocument(ValueError):
    pass


class _ClauseResult(BaseModel):
    clause_id: str
    findings: list[LLMFinding]


class _Results(BaseModel):
    results: list[_ClauseResult]


@dataclass
class Draft:
    """A finding before verification."""
    clause: Clause
    item: ChecklistItem
    risk: str
    explanation: str
    quote: str
    question: str
    source: str


@dataclass
class Stats:
    dropped_unverified: int = 0
    dropped_reasons: list[str] = field(default_factory=list)


def verify_and_build(drafts: list[Draft], doc: ExtractedDoc, stats: Stats) -> list[Finding]:
    """Keep only findings whose quote is really inside their clause."""
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for d in drafts:
        span = find_quote(d.clause.text, d.quote)
        if span is None:
            stats.dropped_unverified += 1
            stats.dropped_reasons.append(f"{d.item.id}: quote not found in {d.clause.id}")
            continue
        key = (d.clause.id, d.item.id)
        if key in seen:
            continue
        seen.add(key)
        start, end = d.clause.start + span[0], d.clause.start + span[1]
        exact_quote = " ".join(doc.text[start:end].split())  # show the document's own words
        findings.append(Finding(
            id=f"f{len(findings) + 1}", clause_id=d.clause.id, clause_title=d.clause.title,
            checklist_id=d.item.id, name=d.item.name, risk=d.risk,  # type: ignore[arg-type]
            explanation=d.explanation, explanation_hi=d.item.explanation_hi, explanation_kn=d.item.explanation_kn,
            quote=exact_quote, question=d.question, why=d.item.why, source=d.source,  # type: ignore[arg-type]
            rects=rects_for_span(doc.lines, start, end),
        ))
    return findings


def rule_drafts(clauses: list[Clause], checklist: Checklist) -> list[Draft]:
    drafts: list[Draft] = []
    for clause in clauses:
        for hit in rule_hits(clause, checklist.items):
            drafts.append(Draft(clause, hit.item, hit.risk, " ".join(hit.item.explanation.split()),
                                clause.text[hit.start:hit.end], hit.item.question, "rules"))
    return drafts


def llm_drafts(clauses: list[Clause], checklist: Checklist, client: llm_mod.LLMClient,
               redactor: Redactor) -> tuple[list[Draft], list[Clause]]:
    """Ask the LLM about clauses with candidate items. Returns drafts and clauses it failed on."""
    matcher = make_matcher(checklist.items)
    by_id = {i.id: i for i in checklist.items}
    jobs: list[tuple[Clause, str, list[ChecklistItem]]] = []
    for clause in clauses:
        if len(clause.text) < MIN_CLAUSE_CHARS:
            continue
        cands: dict[str, ChecklistItem] = {h.item.id: h.item for h in rule_hits(clause, checklist.items)}
        for item, _score in matcher.top(clause.text, k=3):
            cands.setdefault(item.id, item)
        if cands:
            jobs.append((clause, redactor.redact(clause.text), list(cands.values())))

    drafts: list[Draft] = []
    failed: list[Clause] = []
    for i in range(0, len(jobs), LLM_BATCH):
        batch = jobs[i:i + LLM_BATCH]
        parts = []
        for clause, red_text, cands in batch:
            cand_txt = "\n".join(f"  - {c.id}: {c.name}. Look for: {c.look_for}" for c in cands)
            parts.append(f"CLAUSE {clause.id} ({clause.title}):\n\"\"\"{red_text}\"\"\"\nCANDIDATES:\n{cand_txt}")
        try:
            reply = client.complete(llm_mod.ANALYSIS_SYSTEM, "\n\n".join(parts))
            parsed = _Results(**llm_mod.parse_json(reply))
        except (ValidationError, ValueError, KeyError, Exception) as exc:  # network, JSON, schema
            log.warning("LLM batch failed (%s); using rules for %d clauses", type(exc).__name__, len(batch))
            failed.extend(c for c, _, _ in batch)
            continue
        allowed = {c.id: (c, red, {x.id for x in cands}) for c, red, cands in batch}
        for res in parsed.results:
            if res.clause_id not in allowed:
                continue
            clause, red_text, cand_ids = allowed[res.clause_id]
            for f in res.findings:
                if f.checklist_id not in cand_ids:
                    continue
                # The quote is checked against the redacted text the model saw, then mapped back.
                quote = f.quote if find_quote(red_text, f.quote) is None else redactor.restore(f.quote)
                drafts.append(Draft(clause, by_id[f.checklist_id], f.risk, redactor.restore(f.explanation),
                                    quote, redactor.restore(f.question), "llm"))
    return drafts, failed


def llm_group_paragraphs(paras: list[Clause], doc: ExtractedDoc, client: llm_mod.LLMClient,
                         redactor: Redactor) -> list[Clause]:
    """LLM fallback for documents with no numbering: merge paragraphs into titled clauses."""
    listing = "\n".join(f"[{i}] {redactor.redact(p.text)[:400]}" for i, p in enumerate(paras))
    try:
        data = llm_mod.parse_json(client.complete(llm_mod.SPLIT_SYSTEM, listing))
        groups = [(str(g["title"])[:60], [int(x) for x in g["paragraphs"]]) for g in data["clauses"]]
    except Exception:
        return paras
    flat = [i for _, idxs in groups for i in idxs]
    if flat != list(range(len(paras))):  # must cover every paragraph once, in order
        return paras
    out: list[Clause] = []
    for title, idxs in groups:
        first, last = paras[idxs[0]], paras[idxs[-1]]
        out.append(Clause(id=f"c{len(out) + 1}", title=redactor.restore(title) or first.title,
                          text=doc.text[first.start:last.end], start=first.start, end=last.end,
                          rects=rects_for_span(doc.lines, first.start, last.end)))
    return out


def translate_findings(findings: list[Finding], client: llm_mod.LLMClient) -> None:
    """Replace the checklist's generic translations with translations of the LLM's own text."""
    llm_findings = [f for f in findings if f.source == "llm"]
    if not llm_findings:
        return
    for lang, attr in (("Hindi", "explanation_hi"), ("Kannada", "explanation_kn")):
        try:
            payload = {"items": [{"id": f.id, "text": f.explanation} for f in llm_findings]}
            reply = client.complete(llm_mod.TRANSLATE_SYSTEM.format(language=lang), str(payload))
            items = {x["id"]: x["text"] for x in llm_mod.parse_json(reply)["items"]}
            for f in llm_findings:
                if items.get(f.id):
                    setattr(f, attr, items[f.id])
        except Exception as exc:
            log.warning("Translation to %s failed (%s); keeping checklist translation", lang, type(exc).__name__)


def analyze_pdf(data: bytes, filename: str, client: llm_mod.LLMClient | None = None,
                doc_id: str | None = None) -> Analysis:
    doc = extract_pdf(data)
    if not doc.text.strip():
        if doc.ocr_missing:
            raise NotSupportedDocument(
                "This looks like a scanned PDF. Install Tesseract OCR (see README) so TermGuard can read it.")
        raise NotSupportedDocument("No readable text was found in this PDF.")
    doc_type, _scores = detect_doc_type(doc.text)
    if doc_type == "other":
        raise NotSupportedDocument(
            "TermGuard reads rental agreements and job offer letters. This file does not look like either.")
    checklist = load_checklist(doc_type)
    clauses, method = split_clauses(doc)

    redactor = Redactor()
    if method == "paragraphs" and client is not None:
        clauses = llm_group_paragraphs(clauses, doc, client, redactor)
    stats = Stats()
    engine = "rules"
    if client is not None:
        drafts, failed = llm_drafts(clauses, checklist, client, redactor)
        drafts += rule_drafts(failed, checklist)
        engine = "llm" if len(failed) < len(clauses) else "rules"
    else:
        drafts = rule_drafts(clauses, checklist)
        redactor.redact(doc.text)  # still count what would be redacted, for the privacy panel

    findings = verify_and_build(drafts, doc, stats)
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (order[f.risk], f.rects[0].page if f.rects else 0, f.rects[0].y0 if f.rects else 0))
    for i, f in enumerate(findings, 1):
        f.id = f"f{i}"
    if client is not None:
        translate_findings(findings, client)

    now = time.time()
    counts = {lvl: sum(1 for f in findings if f.risk == lvl) for lvl in ("high", "medium", "low")}
    return Analysis(
        id=doc_id or uuid.uuid4().hex[:12], filename=filename, doc_type=doc_type, doc_type_label=LABELS[doc_type],
        engine=engine, pages=doc.pages, ocr_used=any(p.ocr for p in doc.pages), ocr_missing=doc.ocr_missing,
        clauses=clauses, findings=findings, missing=find_missing(doc.text, checklist),
        facts=extract_facts(doc, doc_type), counts=counts, dropped_unverified=stats.dropped_unverified,
        redactions=redactor.total, disclaimer=" ".join(checklist.disclaimer.split()),
        created_at=now, expires_at=now + settings.retention_minutes * 60,
    )
