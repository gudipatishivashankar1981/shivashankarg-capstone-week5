#!/usr/bin/env python3
"""Self-check for the Milestone 1 success criteria.

    python scripts/validate_m1.py            # prints a PASS/FAIL checklist
    python scripts/validate_m1.py --strict   # also fail if golden questions are not human-verified yet

Checks: corpus size and coverage, golden-set composition, required deliverable files,
required ADR sections, Answer schema, and (if present) the DR#1 one-pager length.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED_FILES = [
    "docs/adr/0001-capstone-framing.md",
    "docs/adr/0002-api-contract.md",
    "docs/stakeholder-map.md",
    "src/api/main.py",
    "src/api/auth.py",
    "src/api/logging_middleware.py",
    "src/api/cost_tracking.py",
    "src/pipeline/models.py",
    "data/golden_set_full.jsonl",
    "scripts/run_rag_eval.py",
    "DR1_OnePager.pdf",
]
ADR1_SECTIONS = ["Context", "Problem statement", "EKA scope", "Stakeholders", "KPI targets",
                 "Technology approach", "Alternatives considered", "Trade-offs"]
ADR2_SECTIONS = ["Purpose of the API contract", "/ask endpoint specification", "Schema versioning rules",
                 "Alternatives considered", "Trade-offs", "Future evolution"]

results: list[tuple[str, str, str]] = []  # (status, check, detail)


def check(ok: bool, name: str, detail: str = "", warn_only: bool = False) -> None:
    results.append(("PASS" if ok else ("WARN" if warn_only else "FAIL"), name, detail))


def body_of(path: Path) -> tuple[dict, str]:
    parts = re.split(r"^---\s*$", path.read_text(encoding="utf-8"), flags=re.M, maxsplit=2)
    meta = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
    return meta, parts[2]


def headings(path: Path) -> list[str]:
    found = re.findall(r"^#{1,3}\s+(?:\d+[.)]?\s*)?(.+?)\s*$", path.read_text(encoding="utf-8"), flags=re.M)
    return [h.replace("`", "").lower() for h in found]  # ignore markdown code ticks in headings


def validate_corpus() -> set[str]:
    files = sorted((ROOT / "data" / "corpus").glob("*/*.md"))
    check(10 <= len(files) <= 30, "Corpus has 10-30 documents", f"{len(files)} documents")
    topics: Counter[str] = Counter()
    ids: set[str] = set()
    bad_size, bad_meta = [], []
    for f in files:
        meta, body = body_of(f)
        words = len(body.split())
        ids.add(meta.get("doc_id", "?"))
        topics[meta.get("topic", "?")] += 1
        if not 500 <= words <= 3000:
            bad_size.append(f"{meta.get('doc_id')}={words}")
        if not meta.get("rights_status") or not meta.get("doc_id"):
            bad_meta.append(f.name)
    check(not bad_size, "Every document is 500-3000 words", ", ".join(bad_size) or "all within range")
    check(len(topics) >= 3 and all(n >= 5 for n in topics.values()), "At least 5 documents per major topic",
          ", ".join(f"{t}={n}" for t, n in sorted(topics.items())))
    check(not bad_meta and len(ids) == len(files), "Unique doc ids and rights status recorded", ", ".join(bad_meta) or "ok")
    return ids


def validate_golden(doc_ids: set[str], strict: bool) -> None:
    path = ROOT / "data" / "golden_set_full.jsonl"
    if not path.exists():
        check(False, "Golden set file exists")
        return
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    check(len(rows) == 20, "Golden set has 20 questions", str(len(rows)))
    check(len({r["id"] for r in rows}) == len(rows), "Question ids are unique")
    diff = Counter(r["difficulty"] for r in rows)
    check(diff == Counter(easy=8, medium=8, hard=4), "Difficulty mix is 8 easy / 8 medium / 4 hard", str(dict(diff)))
    check(sum(r["answerable"] for r in rows) >= 16, "At least 16 answerable questions", str(sum(r["answerable"] for r in rows)))
    check(all(r["expected_behavior"] in ("escalate", "refuse") for r in rows if r["difficulty"] == "hard"),
          "Hard questions test escalation / refusal")
    required = ("id", "question", "ideal_answer", "tags", "difficulty")
    check(all(all(r.get(k) for k in required) for r in rows), "Every question has id, question, ideal answer, tags, difficulty")
    check(all(r["difficulty"].capitalize() in r["tags"] for r in rows), "Difficulty label appears in tags")
    unknown = {d for r in rows for d in r["source_docs"]} - doc_ids
    check(not unknown, "Every gold source document exists in the corpus", ", ".join(sorted(unknown)) or "ok")
    multi = [r for r in rows if r["difficulty"] == "medium"]
    check(all(len(r["source_docs"]) >= 2 for r in multi), "Medium questions need 2+ documents (cross-document synthesis)")
    verified = sum(bool(r.get("human_verified")) for r in rows)
    check(verified == len(rows), "Human verification completed for all 20 questions",
          f"{verified}/20 verified - set human_verified=true, verified_by and verified_on after you review each one",
          warn_only=not strict)


def validate_files_and_adrs() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    check(not missing, "All required deliverable files exist", ", ".join(missing) or "ok")
    for rel, wanted in (("docs/adr/0001-capstone-framing.md", ADR1_SECTIONS), ("docs/adr/0002-api-contract.md", ADR2_SECTIONS)):
        p = ROOT / rel
        if p.exists():
            found = headings(p)
            absent = [s for s in wanted if not any(s.lower() in h for h in found)]
            check(not absent, f"{p.name} contains all required sections", ", ".join(absent) or "ok")
    sm = ROOT / "docs" / "stakeholder-map.md"
    if sm.exists():
        personas = len(re.findall(r"^##\s+Persona\s+\d", sm.read_text(encoding="utf-8"), flags=re.M))
        check(3 <= personas <= 5, "Stakeholder map has 3-5 named personas", str(personas))


def validate_schema() -> None:
    from src.pipeline.models import Answer

    expected = {"content", "cost_usd", "retries", "confidence", "sources", "schema_version"}
    check(set(Answer.model_fields) == expected and Answer.model_fields["schema_version"].default == "v1",
          "Answer schema matches the required v1 fields")


def validate_onepager() -> None:
    pdf = ROOT / "DR1_OnePager.pdf"
    if not pdf.exists():
        return
    if not shutil.which("pdftotext"):
        check(False, "DR#1 one-pager length", "pdftotext not installed; check manually (400-500 words)", warn_only=True)
        return
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    words = len(text.split())
    check(400 <= words <= 500, "DR#1 one-pager is 400-500 words", f"{words} words")
    if shutil.which("pdfinfo"):
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        check(pages == 1, "DR#1 one-pager fits on one page", f"{pages} page(s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="treat missing human verification as a failure")
    args = ap.parse_args()

    ids = validate_corpus()
    validate_golden(ids, args.strict)
    validate_files_and_adrs()
    validate_schema()
    validate_onepager()

    width = max(len(n) for _, n, _ in results)
    for status, name, detail in results:
        print(f"[{status}] {name.ljust(width)}  {detail}")
    fails = sum(s == "FAIL" for s, _, _ in results)
    warns = sum(s == "WARN" for s, _, _ in results)
    print(f"\n{len(results) - fails - warns} passed, {warns} warning(s), {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
