"""Labelling helper: mark which checklist items truly apply to each clause of a PDF.

    python eval/label_tool.py samples/private/my_agreement.pdf

For each clause you see its text and the checklist. Type the numbers of the items that
apply (for example "2 5"), press Enter for none, "b" to go back, or "q" to save and quit.
Labels are written to eval/labels/<file name>.json. Keep real documents in
samples/private/ (git-ignored); only the labels file is safe to commit, and it stores
just the first 60 characters of each clause, so redact names before labelling.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.checklist import load_checklist  # noqa: E402
from app.clauses import split_clauses  # noqa: E402
from app.doctype import detect_doc_type  # noqa: E402
from app.extract import extract_pdf  # noqa: E402

LABELS = ROOT / "eval" / "labels"


def main(path: Path) -> None:
    doc = extract_pdf(path.read_bytes())
    doc_type, _ = detect_doc_type(doc.text)
    if doc_type == "other":
        sys.exit("This does not look like a rental agreement or offer letter.")
    items = load_checklist(doc_type).items
    clauses, _ = split_clauses(doc)
    out_path = LABELS / f"{path.stem}.json"
    previous = {}
    if out_path.exists():
        previous = {r["clause_start"]: r["labels"] for r in json.loads(out_path.read_text())["clauses"]}
    menu = "\n".join(f"  {n:>2}. {it.name}" for n, it in enumerate(items, 1))
    rows: list[dict] = [{"clause_start": c.text[:60], "labels": previous.get(c.text[:60], [])} for c in clauses]
    i = 0
    while i < len(clauses):
        c = clauses[i]
        print("\n" + "=" * 72)
        print(f"Clause {i + 1}/{len(clauses)}: {c.title}")
        print(textwrap.fill(" ".join(c.text.split()), 72))
        print("\nChecklist:\n" + menu)
        if rows[i]["labels"]:
            print(f"Current: {rows[i]['labels']}")
        ans = input("Items that apply (numbers, Enter = none, b = back, q = quit): ").strip().lower()
        if ans == "q":
            break
        if ans == "b":
            i = max(0, i - 1)
            continue
        picks = [items[int(x) - 1].id for x in ans.replace(",", " ").split() if x.isdigit() and 0 < int(x) <= len(items)]
        rows[i]["labels"] = picks
        i += 1
    LABELS.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"document": path.name, "kind": doc_type, "labelled_by": "human",
                                    "clauses": rows}, indent=2), encoding="utf-8")
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
