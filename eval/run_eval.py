"""Evaluate TermGuard against the labelled clauses in eval/labels/.

    python eval/run_eval.py          # rule engine (offline)
    python eval/run_eval.py --llm    # use the LLM from .env

Reports precision and recall per checklist item and overall, findings dropped by the
quote check, and the reading level of the explanations. Writes eval/results.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.analyzer import analyze_pdf  # noqa: E402
from app.checklist import load_checklist  # noqa: E402
from app.facts import flesch_reading_ease  # noqa: E402
from app.llm import default_client  # noqa: E402
from app.verify import find_quote  # noqa: E402

LABELS = ROOT / "eval" / "labels"
SEARCH = [ROOT / "samples" / "public", ROOT / "samples" / "private"]


def find_pdf(name: str) -> Path | None:
    for d in SEARCH:
        if (d / name).exists():
            return d / name
    return None


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def main(use_llm: bool) -> None:
    client = default_client() if use_llm else None
    if use_llm and client is None:
        sys.exit("Set LLM_API_KEY in .env to run with the LLM.")
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)
    names: dict[str, str] = {}
    failures: list[str] = []
    explanations: list[str] = []
    dropped = n_clauses = n_findings = n_docs = 0
    uncited = 0
    started = time.time()

    for label_file in sorted(LABELS.glob("*.json")):
        spec = json.loads(label_file.read_text(encoding="utf-8"))
        pdf = find_pdf(spec["document"])
        if not pdf:
            print(f"skip {spec['document']} (PDF not found)")
            continue
        a = analyze_pdf(pdf.read_bytes(), pdf.name, client=client)
        n_docs += 1
        for it in load_checklist(a.doc_type).items:
            names[it.id] = it.name
        text = "\n".join(c.text for c in a.clauses)
        # Map each labelled clause to the extracted clause that contains its first words.
        gold: dict[str, set[str]] = {c.id: set() for c in a.clauses}
        for row in spec["clauses"]:
            span = find_quote(text, row["clause_start"][:40])
            if span is None:
                failures.append(f"`{pdf.name}`: labelled clause not found in extraction: \"{row['clause_start'][:40]}…\"")
                for lab in row["labels"]:
                    fn[lab] += 1
                continue
            offset = 0
            for c in a.clauses:
                if offset <= span[0] < offset + len(c.text) + 1:
                    gold[c.id] |= set(row["labels"])
                    break
                offset += len(c.text) + 1
        pred: dict[str, set[str]] = defaultdict(set)
        quotes: dict[tuple[str, str], str] = {}
        for f in a.findings:
            pred[f.clause_id].add(f.checklist_id)
            quotes[(f.clause_id, f.checklist_id)] = f.quote
            explanations.append(f.explanation)
            if not f.quote or not f.rects:
                uncited += 1
        n_findings += len(a.findings)
        n_clauses += len(a.clauses)
        dropped += a.dropped_unverified
        titles = {c.id: c.title for c in a.clauses}
        for cid in gold:
            for lab in gold[cid] & pred[cid]:
                tp[lab] += 1
            for lab in pred[cid] - gold[cid]:
                fp[lab] += 1
                failures.append(f"False alarm `{lab}` in `{pdf.name}` / {titles[cid]}: \"{quotes[(cid, lab)][:110]}\"")
            for lab in gold[cid] - pred[cid]:
                fn[lab] += 1
                failures.append(f"Missed `{lab}` in `{pdf.name}` / {titles[cid]}")

    labels = sorted(set(tp) | set(fp) | set(fn))
    T, P, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
    precision = T / (T + P) if T + P else 0.0
    recall = T / (T + N) if T + N else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    ease = flesch_reading_ease(" ".join(explanations)) if explanations else 0.0
    engine = "LLM + quote check" if use_llm else "rule engine (offline)"

    lines = [
        "# TermGuard evaluation results", "",
        f"Engine: **{engine}**. Documents: {n_docs}. Clauses: {n_clauses}. Findings shown: {n_findings}. "
        f"Run time: {time.time() - started:.1f}s.", "",
        "> These numbers come from the synthetic sample set in `samples/public/`, labelled clause by clause.",
        "> The rules were written alongside these samples, so treat the scores as optimistic. Add your own",
        "> redacted documents to `samples/private/`, label them with `eval/label_tool.py`, and rerun.", "",
        "## Overall", "",
        "| Metric | Value |", "|---|---|",
        f"| Precision | {pct(precision)} ({T} of {T + P} findings were correct) |",
        f"| Recall | {pct(recall)} ({T} of {T + N} labelled risks were found) |",
        f"| F1 | {f1:.2f} |",
        f"| Findings dropped by the quote check | {dropped} |",
        f"| Findings shown without a verified quote | {uncited} |",
        f"| Reading ease of explanations (Flesch, higher is easier) | {ease} |", "",
        "## Per checklist item", "",
        "| Item | Name | TP | FP | FN | Precision | Recall |", "|---|---|---|---|---|---|---|",
    ]
    for lab in labels:
        t, p, n = tp[lab], fp[lab], fn[lab]
        lines.append(f"| `{lab}` | {names.get(lab, '')} | {t} | {p} | {n} | "
                     f"{pct(t / (t + p)) if t + p else '-'} | {pct(t / (t + n)) if t + n else '-'} |")
    lines += ["", "## Failure cases", ""]
    lines += [f"- {f}" for f in failures] or ["- None on this set."]
    lines += ["", "## Why recall matters more here", "",
              "Missing a risky clause costs the user far more than reading one extra explanation, so the",
              "checklist patterns lean towards recall. Precision is protected differently: every finding",
              "must quote the document, so a false alarm is visible and easy to dismiss."]
    out = ROOT / "eval" / "results.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:22]))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use the LLM configured in .env")
    main(ap.parse_args().llm)
