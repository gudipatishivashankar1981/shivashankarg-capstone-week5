"""Tests for the evaluation harness (scripts/run_rag_eval.py)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from src.pipeline.models import Answer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_rag_eval", ROOT / "scripts" / "run_rag_eval.py")
ev = importlib.util.module_from_spec(spec)
sys.modules["run_rag_eval"] = ev  # required so @dataclass can resolve the module
spec.loader.exec_module(ev)


def item(**kw):
    base = dict(id="t1", question="q?", ideal_answer="a", tags=["HR"], difficulty="easy", expected_behavior="answer",
                source_docs=["HR-001"], must_include=["20 working days", "USD 1,000"])
    base.update(kw)
    return base


def ans(content="", confidence=0.9, sources=("HR-001#2",)):
    return Answer(content=content, cost_usd=0.001, retries=0, confidence=confidence, sources=list(sources))


def test_answerable_pass_requires_facts_sources_and_confidence():
    good = ev.score_one(item(), ans("You get 20 working days and a budget of USD 1000."), 0.01, None)
    assert good["passed"] and good["fact_coverage"] == 1.0 and good["source_recall"] == 1.0

    low_conf = ev.score_one(item(), ans("20 working days USD 1,000", confidence=0.2), 0.01, None)
    assert not low_conf["passed"] and low_conf["escalated"]

    no_facts = ev.score_one(item(), ans("I do not know."), 0.01, None)
    assert not no_facts["passed"] and no_facts["fact_coverage"] == 0.0

    wrong_doc = ev.score_one(item(), ans("20 working days USD 1,000", sources=["IT-001#1"]), 0.01, None)
    assert not wrong_doc["passed"] and wrong_doc["source_recall"] == 0.0


def test_hard_questions_pass_only_when_escalated():
    hard = item(expected_behavior="escalate", must_include=[], difficulty="hard")
    assert ev.score_one(hard, ans("Contact HR.", confidence=0.1, sources=()), 0.01, None)["passed"]
    confident_guess = ev.score_one(hard, ans("Sabbatical is 3 months.", confidence=0.9), 0.01, None)
    assert not confident_guess["passed"] and confident_guess["fact_coverage"] is None


def test_errors_count_as_failures():
    r = ev.score_one(item(), None, 0.5, "URLError: boom")
    assert not r["passed"] and r["error"] and r["escalated"] is None


def test_normalisation_and_source_ids():
    assert ev.norm("USD 1,000") == ev.norm("usd  1000")
    assert ev.doc_ids(["HR-001#2", "HR-001#3", "IT-002"]) == ["HR-001", "IT-002"]


def test_corpus_loads_and_chunks():
    chunks = ev.load_corpus(ROOT / "data" / "corpus")
    assert {c.doc_id for c in chunks} >= {"HR-001", "IT-006", "OPS-005"}
    assert all(c.tokens for c in chunks)


def test_fake_system_is_deterministic_and_respects_contract():
    system = ev.FakeEKA(ev.load_corpus(ROOT / "data" / "corpus"))
    a1 = system.answer("How many days of annual leave do employees receive?")
    a2 = system.answer("How many days of annual leave do employees receive?")
    assert a1 == a2 and a1.sources[0].startswith("HR-001") and "20 working days" in a1.content
    nonsense = system.answer("zxqv blorp wibble quux")
    assert nonsense.needs_escalation() and nonsense.sources == []


def test_end_to_end_cli_writes_results_and_compares(tmp_path, capsys):
    rc = ev.main(["--fake", "--label", "unit", "--out-dir", str(tmp_path)])
    assert rc == 0
    saved = json.loads((tmp_path / "unit.json").read_text())
    assert len(saved["results"]) == 20 and saved["config"]["cost_is_simulated"] is True
    assert set(saved["summary"]["by_difficulty"]) == {"easy", "medium", "hard"}

    rc = ev.main(["--fake", "--label", "unit2", "--compare", "unit", "--out-dir", str(tmp_path), "--min-pass-rate", "1.0"])
    out = capsys.readouterr().out
    assert rc == 1 and "regressions  : none" in out  # identical run, but the pass-rate gate fails


def test_cli_requires_a_system_and_valid_label():
    with pytest.raises(SystemExit):
        ev.parse_args([])
    with pytest.raises(SystemExit):
        ev.parse_args(["--fake", "--label", "bad label/../x"])
    with pytest.raises(SystemExit):
        ev.parse_args(["--endpoint", "http://x/ask"])  # token missing
