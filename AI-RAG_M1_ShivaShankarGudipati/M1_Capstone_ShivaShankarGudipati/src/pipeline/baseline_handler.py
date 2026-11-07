"""Opt-in handler that answers from the corpus using the offline lexical baseline.

Enable it with ``EKA_HANDLER=baseline``. It reuses the BM25 + extractive logic from
``scripts/run_rag_eval.py`` (the same system the ``--fake`` evaluation scores), so
what you see through the API is exactly what the baseline numbers describe:
sometimes right on single-document questions, weak on cross-document ones, and
imperfect at knowing when to escalate. It is a demo and a comparison floor, not
the real RAG pipeline.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from src.pipeline.models import Answer

ROOT = Path(__file__).resolve().parents[2]


def _load_eval_module():
    path = ROOT / "scripts" / "run_rag_eval.py"
    spec = importlib.util.spec_from_file_location("run_rag_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_rag_eval"] = module  # needed so @dataclass can resolve the module
    spec.loader.exec_module(module)
    return module


class BaselineHandler:
    name = "lexical-baseline"

    def __init__(self, corpus_dir: Path | None = None) -> None:
        ev = _load_eval_module()
        self._system = ev.FakeEKA(ev.load_corpus(corpus_dir or ROOT / "data" / "corpus"))

    def answer(self, question: str, *, top_k: int = 5) -> Answer:
        result = self._system.answer(question, top_k=min(top_k, 5))
        # The baseline makes no model calls; its cost figure is only simulated, so report 0.
        return result.model_copy(update={"cost_usd": 0.0})
