#!/usr/bin/env python3
"""Baseline evaluation harness for the Enterprise Knowledge Assistant (EKA).

Runs every question in data/golden_set_full.jsonl through an EKA "system under test",
scores the answers, prints a report and saves machine-readable results so that
later milestones can be compared against today's baseline.

Usage (from the scripts/ folder or the project root)::

    python run_rag_eval.py --fake --label baseline            # offline baseline, no API, no cost
    python run_rag_eval.py --endpoint http://localhost:8000/ask --token $EKA_API_TOKEN --label api-check
    python run_rag_eval.py --fake --label rerun --compare baseline   # show deltas vs. saved baseline
    python run_rag_eval.py --fake --label ci --min-pass-rate 0.5     # exit 1 if overall pass rate < 0.5

Systems under test
------------------
--fake       Built-in, dependency-free *lexical* baseline: BM25 retrieval over the corpus and
             extractive answers, with a coverage-based confidence. It makes no LLM calls.
             It is deliberately simple and UNTUNED: it is the floor every future RAG
             version must beat. Cost is *simulated* (what a small hosted LLM would charge
             to read the same context) so the cost-tracking path is exercised end to end.
--endpoint   Calls a live POST /ask endpoint (ADR 0002) and scores the real responses.

Scoring (per question)
----------------------
* behavior_correct  answerable questions must be answered (confidence >= ESCALATION_THRESHOLD);
                    refusal/escalation questions must be escalated (confidence < threshold).
* fact_coverage     share of the question's `must_include` key facts found in the answer text.
* source_recall     share of gold `source_docs` that appear in the answer's `sources`.
* source_precision  share of cited documents that are gold documents.
* passed            answerable: behavior_correct AND fact_coverage >= 0.75 AND source_recall >= 0.5
                    hard (refuse/escalate): behavior_correct.

Sponsor-KPI proxies reported in the summary (see ADR 0001): question-resolution proxy,
answer-accuracy proxy, escalation correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.models import ESCALATION_MESSAGE, ESCALATION_THRESHOLD, Answer  # noqa: E402

DEFAULT_GOLDEN = ROOT / "data" / "golden_set_full.jsonl"
DEFAULT_CORPUS = ROOT / "data" / "corpus"
DEFAULT_OUT = ROOT / "eval_results"

FACT_COVERAGE_MIN = 0.75
SOURCE_RECALL_MIN = 0.50

# Illustrative prices (USD per 1M tokens) for the *simulated* cost of the fake pipeline.
SIM_PRICE_IN_PER_M = 0.15
SIM_PRICE_OUT_PER_M = 0.60

STOPWORDS = frozenset(
    "a an and are as at be been but by can could do does for from had has have how i if in into is it its "
    "me my of on or our should so than that the their them then there these they this to us was we were "
    "what when where which who whom why will with would you your".split()
)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_golden(path: Path) -> list[dict]:
    items = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})") from exc
        for key in ("id", "question", "ideal_answer", "tags", "difficulty", "expected_behavior", "source_docs"):
            if key not in item:
                raise SystemExit(f"{path}:{lineno}: missing required field '{key}'")
        items.append(item)
    if not items:
        raise SystemExit(f"{path}: no questions found")
    return items


@dataclass
class Chunk:
    doc_id: str
    section: str  # e.g. "2"
    text: str
    tokens: list[str]

    @property
    def source(self) -> str:
        return f"{self.doc_id}#{self.section}" if self.section else self.doc_id


def tokenize(text: str) -> list[str]:
    out = []
    for tok in re.findall(r"[a-z0-9]+", text.lower()):
        if tok in STOPWORDS:
            continue
        if len(tok) > 3 and tok.endswith("s"):  # crude plural stemming
            tok = tok[:-1]
        out.append(tok)
    return out


def load_corpus(corpus_dir: Path) -> list[Chunk]:
    """Split every corpus document into section-level chunks (split on '## ' headings)."""
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*/*.md")):
        text = path.read_text(encoding="utf-8")
        parts = re.split(r"^---\s*$", text, flags=re.M, maxsplit=2)
        meta = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
        doc_id, title = meta["doc_id"], meta.get("title", "")
        for block in re.split(r"^## ", parts[2], flags=re.M)[1:]:
            heading, _, body = block.partition("\n")
            m = re.match(r"(\d+)\.\s*(.*)", heading.strip())
            section, head_text = (m.group(1), m.group(2)) if m else ("", heading.strip())
            body = body.strip()
            if body:
                full = f"{title}. {head_text}. {body}"
                chunks.append(Chunk(doc_id, section, body, tokenize(full)))
    if not chunks:
        raise SystemExit(f"No corpus documents found under {corpus_dir}")
    return chunks


def sha256_of(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Systems under test
# --------------------------------------------------------------------------- #
class FakeEKA:
    """Offline lexical baseline: BM25 retrieval + extractive answer + coverage confidence."""

    name = "fake-lexical-bm25"

    def __init__(self, chunks: list[Chunk], top_k: int = 3, k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks, self.top_k, self.k1, self.b = chunks, top_k, k1, b
        self.n = len(chunks)
        self.avgdl = sum(len(c.tokens) for c in chunks) / self.n
        df: Counter[str] = Counter()
        for c in chunks:
            df.update(set(c.tokens))
        self.idf = {t: math.log(1 + (self.n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.tf = [Counter(c.tokens) for c in chunks]

    def _bm25(self, q_terms: list[str], i: int) -> float:
        tf, dl, score = self.tf[i], len(self.chunks[i].tokens), 0.0
        for t in q_terms:
            f = tf.get(t, 0)
            if f:
                score += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return score

    def _coverage(self, q_terms: list[str], tokens: set[str]) -> float:
        """IDF-weighted share of the question's known terms that the chunk contains."""
        known = [t for t in set(q_terms) if t in self.idf]
        total = sum(self.idf[t] for t in known)
        # Terms never seen in the corpus count against coverage (the corpus cannot answer them).
        unseen = len(set(q_terms)) - len(known)
        total += unseen * (max(self.idf.values()) if unseen else 0.0)
        return sum(self.idf[t] for t in known if t in tokens) / total if total else 0.0

    def answer(self, question: str, *, top_k: int | None = None) -> Answer:
        k = top_k or self.top_k
        q_terms = tokenize(question)
        ranked = sorted(range(self.n), key=lambda i: self._bm25(q_terms, i), reverse=True)[:k]
        confidence = round(self._coverage(q_terms, set(self.chunks[ranked[0]].tokens)), 4) if ranked else 0.0

        in_tokens = len(question) / 4 + sum(len(self.chunks[i].text) for i in ranked) / 4
        if confidence < ESCALATION_THRESHOLD:
            content, sources = ESCALATION_MESSAGE, []
        else:
            sentences = []  # (score, text, source)
            for i in ranked:
                for sent in re.split(r"(?<=[.!?])\s+|\n+", self.chunks[i].text):
                    s_terms = set(tokenize(sent))
                    if s_terms:
                        sentences.append((sum(self.idf[t] for t in set(q_terms) if t in s_terms), sent.strip(), self.chunks[i].source))
            best = sorted(sentences, key=lambda x: x[0], reverse=True)[:3]
            content = " ".join(s for _, s, _ in best)
            sources = list(dict.fromkeys(src for _, _, src in best))
        out_tokens = len(content) / 4
        cost = (in_tokens * SIM_PRICE_IN_PER_M + out_tokens * SIM_PRICE_OUT_PER_M) / 1e6
        return Answer(content=content, cost_usd=round(cost, 8), retries=0, confidence=confidence, sources=sources)


class RemoteEKA:
    """Calls a live POST /ask endpoint that follows the ADR 0002 contract."""

    def __init__(self, endpoint: str, token: str, timeout: float = 60.0) -> None:
        self.name, self.endpoint, self.token, self.timeout = f"remote:{endpoint}", endpoint, token, timeout

    def answer(self, question: str, *, top_k: int | None = None) -> Answer:
        payload = {"question": question}
        if top_k:
            payload["top_k"] = top_k
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - user-supplied URL by design
            return Answer.model_validate_json(resp.read())


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace(",", "")).strip()


def doc_ids(sources: list[str]) -> list[str]:
    return list(dict.fromkeys(s.split("#", 1)[0] for s in sources))


def score_one(item: dict, answer: Answer | None, latency_s: float, error: str | None) -> dict:
    expected = item["expected_behavior"]
    base = {
        "id": item["id"],
        "difficulty": item["difficulty"],
        "tags": item["tags"],
        "expected_behavior": expected,
        "question": item["question"],
        "latency_ms": round(latency_s * 1000, 2),
        "error": error,
    }
    if answer is None:
        return {**base, "answer": None, "escalated": None, "behavior_correct": False, "fact_coverage": 0.0,
                "source_recall": 0.0, "source_precision": 0.0, "confidence": 0.0, "cost_usd": 0.0,
                "retries": 0, "passed": False}

    escalated = answer.needs_escalation()
    behavior_correct = (not escalated) if expected == "answer" else escalated
    gold_docs, cited = set(item["source_docs"]), doc_ids(answer.sources)
    facts = item.get("must_include") or []
    coverage = sum(norm(f) in norm(answer.content) for f in facts) / len(facts) if facts else 1.0
    recall = len(gold_docs & set(cited)) / len(gold_docs) if gold_docs else 1.0
    precision = len(gold_docs & set(cited)) / len(cited) if cited else 0.0

    if expected == "answer":
        passed = behavior_correct and coverage >= FACT_COVERAGE_MIN and recall >= SOURCE_RECALL_MIN
        scores = {"fact_coverage": round(coverage, 4), "source_recall": round(recall, 4),
                  "source_precision": round(precision, 4)}
    else:  # refusal / escalation: only the behaviour is scored; citation metrics do not apply
        passed = behavior_correct
        scores = {"fact_coverage": None, "source_recall": None, "source_precision": None}
    return {**base, "answer": answer.model_dump(), "escalated": escalated, "behavior_correct": behavior_correct,
            **scores, "confidence": answer.confidence, "cost_usd": answer.cost_usd, "retries": answer.retries,
            "passed": passed}


def mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 4) if values else 0.0


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, math.ceil(pct / 100 * len(ordered)) - 1)], 2)


def summarise(results: list[dict]) -> dict:
    def block(rows: list[dict]) -> dict:
        answerable = [r for r in rows if r["expected_behavior"] == "answer"]
        return {
            "n": len(rows),
            "pass_rate": mean([r["passed"] for r in rows]),
            "behavior_accuracy": mean([r["behavior_correct"] for r in rows]),
            "fact_coverage": mean([r["fact_coverage"] for r in answerable]) if answerable else None,
            "source_recall": mean([r["source_recall"] for r in answerable]) if answerable else None,
            "source_precision": mean([r["source_precision"] for r in answerable]) if answerable else None,
            "mean_confidence": mean([r["confidence"] for r in rows]),
        }

    by_difficulty = defaultdict(list)
    for r in results:
        by_difficulty[r["difficulty"]].append(r)

    answerable = [r for r in results if r["expected_behavior"] == "answer"]
    hard = [r for r in results if r["expected_behavior"] != "answer"]
    tp = sum(1 for r in hard if r["escalated"])
    fp = sum(1 for r in answerable if r["escalated"])
    latencies = [r["latency_ms"] for r in results]
    return {
        "overall": block(results),
        "by_difficulty": {d: block(rows) for d, rows in sorted(by_difficulty.items())},
        "escalation": {
            "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
            "recall": round(tp / len(hard), 4) if hard else 0.0,
            "false_escalations": fp,
            "missed_escalations": len(hard) - tp,
        },
        "kpi_proxies": {
            "question_resolution_rate": mean([not r["escalated"] for r in answerable if r["escalated"] is not None]),
            "answer_accuracy": mean([r["passed"] for r in answerable]),
            "escalation_correctness": mean([r["behavior_correct"] for r in hard]),
        },
        "confidence": {
            "mean_when_passed": mean([r["confidence"] for r in results if r["passed"]]),
            "mean_when_failed": mean([r["confidence"] for r in results if not r["passed"]]),
        },
        "latency_ms": {"p50": percentile(latencies, 50), "p95": percentile(latencies, 95)},
        "cost_usd": {"total": round(sum(r["cost_usd"] for r in results), 6),
                     "per_question": mean([r["cost_usd"] for r in results])},
        "mean_retries": mean([r["retries"] for r in results]),
        "errors": sum(1 for r in results if r["error"]),
    }


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def pct(x: float | None) -> str:
    return "  n/a" if x is None else f"{x * 100:5.1f}%"


def num(x: float | None, width: int = 7) -> str:
    return f"{'-':>{width}}" if x is None else f"{x:>{width}.2f}"


def print_report(label: str, mode: str, summary: dict, results: list[dict], verbose: bool) -> None:
    o, line = summary["overall"], "-" * 78
    print(f"\n{line}\nEKA evaluation | label={label} | system={mode} | {o['n']} questions\n{line}")
    print(f"{'slice':<10}{'n':>3}{'pass':>9}{'behavior':>10}{'facts':>9}{'recall':>9}{'precis.':>9}{'conf':>8}")
    for name, b in [("overall", o), *summary["by_difficulty"].items()]:
        print(f"{name:<10}{b['n']:>3}{pct(b['pass_rate']):>9}{pct(b['behavior_accuracy']):>10}"
              f"{pct(b['fact_coverage']):>9}{pct(b['source_recall']):>9}{pct(b['source_precision']):>9}{b['mean_confidence']:>8.2f}")
    k, e = summary["kpi_proxies"], summary["escalation"]
    print(f"\nKPI proxies : resolution={pct(k['question_resolution_rate']).strip()}  accuracy={pct(k['answer_accuracy']).strip()}"
          f"  escalation-correctness={pct(k['escalation_correctness']).strip()}")
    print(f"Escalation  : precision={pct(e['precision']).strip()}  recall={pct(e['recall']).strip()}"
          f"  false={e['false_escalations']}  missed={e['missed_escalations']}")
    print(f"Confidence  : passed={summary['confidence']['mean_when_passed']:.2f}  failed={summary['confidence']['mean_when_failed']:.2f}")
    print(f"Latency ms  : p50={summary['latency_ms']['p50']}  p95={summary['latency_ms']['p95']}")
    print(f"Cost USD    : total={summary['cost_usd']['total']}  per-question={summary['cost_usd']['per_question']}"
          f"{'  (simulated)' if mode.startswith('fake') else ''}   mean retries={summary['mean_retries']}   errors={summary['errors']}")
    print(f"\n{'id':<5}{'diff':<8}{'expect':<10}{'got':<10}{'conf':>6}{'facts':>7}{'recall':>8}  result")
    for r in results:
        got = "error" if r["escalated"] is None else ("escalate" if r["escalated"] else "answer")
        print(f"{r['id']:<5}{r['difficulty']:<8}{r['expected_behavior']:<10}{got:<10}{r['confidence']:>6.2f}"
              f"{num(r['fact_coverage'])}{num(r['source_recall'], 8)}  {'PASS' if r['passed'] else 'FAIL'}")
        if verbose and r["answer"]:
            print(f"      Q: {r['question']}\n      A: {r['answer']['content'][:220]}\n      sources: {r['answer']['sources']}")


def print_comparison(old: dict, new_label: str, new_summary: dict, new_results: list[dict]) -> None:
    print(f"\nComparison: {new_label} vs {old['label']} (baseline run {old['timestamp']})")
    metrics = [("pass_rate", "overall pass rate"), ("fact_coverage", "fact coverage"), ("source_recall", "source recall"),
               ("behavior_accuracy", "behavior accuracy")]
    for key, name in metrics:
        a, b = old["summary"]["overall"][key], new_summary["overall"][key]
        delta = f"({(b - a) * 100:+.1f} pts)" if a is not None and b is not None else ""
        print(f"  {name:<20}{pct(a)} -> {pct(b)}   {delta}")
    a, b = old["summary"]["cost_usd"]["per_question"], new_summary["cost_usd"]["per_question"]
    print(f"  {'cost / question':<20}{a:.6f} -> {b:.6f} USD")
    old_pass = {r["id"]: r["passed"] for r in old["results"]}
    fixed = [r["id"] for r in new_results if r["passed"] and old_pass.get(r["id"]) is False]
    regressed = [r["id"] for r in new_results if not r["passed"] and old_pass.get(r["id"]) is True]
    print(f"  newly passing: {fixed or 'none'}\n  regressions  : {regressed or 'none'}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the EKA golden-set evaluation.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fake", action="store_true", help="use the built-in offline lexical baseline (no API calls)")
    mode.add_argument("--endpoint", help="URL of a live POST /ask endpoint to evaluate")
    p.add_argument("--token", default=os.getenv("EKA_API_TOKEN"), help="bearer token for --endpoint (or env EKA_API_TOKEN)")
    p.add_argument("--label", default="baseline", help="name of this run; results saved as <out-dir>/<label>.json")
    p.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--top-k", type=int, default=3, help="passages retrieved per question (default 3)")
    p.add_argument("--compare", metavar="LABEL", help="compare against a previously saved run label")
    p.add_argument("--min-pass-rate", type=float, help="exit with status 1 if the overall pass rate is below this value")
    p.add_argument("--verbose", action="store_true", help="print question and answer text for every item")
    args = p.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.label):
        p.error("--label may contain only letters, digits, '.', '_' and '-'")
    if args.endpoint and not args.token:
        p.error("--endpoint needs --token (or EKA_API_TOKEN)")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    golden = load_golden(args.golden)
    corpus_files = sorted(args.corpus.glob("*/*.md"))
    chunks = load_corpus(args.corpus)

    system = FakeEKA(chunks, top_k=args.top_k) if args.fake else RemoteEKA(args.endpoint, args.token)
    results = []
    for item in golden:
        started, answer, error = time.perf_counter(), None, None
        try:
            answer = system.answer(item["question"], top_k=args.top_k)
        except (urllib.error.URLError, OSError, ValueError) as exc:  # network, HTTP and schema errors
            error = f"{type(exc).__name__}: {exc}"
        results.append(score_one(item, answer, time.perf_counter() - started, error))

    summary = summarise(results)
    print_report(args.label, system.name, summary, results, args.verbose)

    payload = {
        "label": args.label,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "system": system.name,
        "config": {
            "top_k": args.top_k,
            "escalation_threshold": ESCALATION_THRESHOLD,
            "fact_coverage_min": FACT_COVERAGE_MIN,
            "source_recall_min": SOURCE_RECALL_MIN,
            "golden_sha256": sha256_of([args.golden]),
            "corpus_sha256": sha256_of(corpus_files),
            "n_documents": len(corpus_files),
            "n_chunks": len(chunks),
            "cost_is_simulated": bool(args.fake),
        },
        "summary": summary,
        "results": results,
    }

    if args.compare:
        old_path = args.out_dir / f"{args.compare}.json"
        if old_path.exists():
            print_comparison(json.loads(old_path.read_text()), args.label, summary, results)
        else:
            print(f"\n(no saved run named '{args.compare}' in {args.out_dir}; skipping comparison)")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{args.label}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved results -> {out_path}")

    if args.min_pass_rate is not None and summary["overall"]["pass_rate"] < args.min_pass_rate:
        print(f"FAILED: overall pass rate {summary['overall']['pass_rate']:.2f} < required {args.min_pass_rate:.2f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
