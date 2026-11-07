"""Answer handlers: the seam between the HTTP layer and the (future) RAG pipeline.

Milestone 1 ships only :class:`PlaceholderHandler`. Later milestones add a
retrieval-augmented handler that implements the same ``AnswerHandler`` protocol,
so the API contract, authentication, logging and cost tracking never change.
"""

from __future__ import annotations

from typing import Protocol

from src.pipeline.models import ESCALATION_MESSAGE, Answer

PLACEHOLDER_NOTICE = (
    "[PLACEHOLDER] The Enterprise Knowledge Assistant retrieval pipeline is not connected yet "
    "(Milestone 1 skeleton), so no answer could be generated. "
)


class AnswerHandler(Protocol):
    """Anything that can turn a question into an :class:`Answer`."""

    name: str

    def answer(self, question: str, *, top_k: int = 5) -> Answer: ...


class PlaceholderHandler:
    """Returns a clearly-labelled, zero-cost, zero-confidence answer.

    Because confidence is 0.0 the response already follows the v1 escalation
    convention: clients route the employee to a human instead of trusting it.
    """

    name = "placeholder"

    def answer(self, question: str, *, top_k: int = 5) -> Answer:  # noqa: ARG002 - interface parity
        return Answer(
            content=PLACEHOLDER_NOTICE + ESCALATION_MESSAGE,
            cost_usd=0.0,
            retries=0,
            confidence=0.0,
            sources=[],
        )
