"""Contract models for the Enterprise Knowledge Assistant (EKA) API.

The ``Answer`` model below is the *v1 answer schema* defined in
ADR 0002 (docs/adr/0002-api-contract.md). It is the single response shape
returned by ``POST /ask`` and the shape the evaluation harness scores.

Contract rules (see ADR 0002):
  * Fields may be ADDED to v1 only as optional fields with defaults.
  * Fields must never be removed, renamed, retyped or change meaning in v1.
    Any such change is a breaking change and requires ``schema_version = "v2"``
    and a new ``/v2/ask`` path.
  * ``tests/test_models.py`` freezes the v1 field set to catch accidents.

Escalation convention (v1): the API has no separate "escalated" flag yet.
A response with ``confidence < ESCALATION_THRESHOLD`` MUST be treated by
clients as "the assistant could not answer reliably - route the employee to a
human". In that case ``content`` begins with the standard escalation message and
``sources`` may be empty. A dedicated ``escalated`` flag is planned as an
additive, backward-compatible change (ADR 0002, "Future evolution").
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "v1"

# Answers below this confidence must be escalated to a human (ADR 0001, KPI guardrails).
ESCALATION_THRESHOLD = 0.40

ESCALATION_MESSAGE = (
    "I couldn't find a reliable answer to this in the approved knowledge base. "
    "Please contact the HR Service Desk (hrdesk@meridian.example) for people and policy "
    "questions, or the IT Helpdesk (ServiceHub, extension 5555) for technology questions."
)


class Answer(BaseModel):
    """Answer returned by the EKA for one employee question (schema v1)."""

    model_config = ConfigDict(extra="forbid")

    content: str
    cost_usd: float = Field(ge=0, description="Total model and retrieval cost for this answer, in USD.")
    retries: int = Field(ge=0, description="Number of generation/retrieval retries used.")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Calibrated confidence that the answer is correct and grounded."
    )
    sources: list[str] = Field(
        description='Citations as "<doc_id>" or "<doc_id>#<section>", e.g. "HR-001#2.1".'
    )
    schema_version: str = "v1"

    def needs_escalation(self) -> bool:
        """True when clients must route the employee to a human (see module docstring)."""
        return self.confidence < ESCALATION_THRESHOLD


# --------------------------------------------------------------------------- #
# Request / auxiliary models (not part of the Answer schema)
# --------------------------------------------------------------------------- #
class AskRequest(BaseModel):
    """Body of ``POST /ask``."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=3, max_length=2000, description="Employee question in natural language.")
    top_k: int = Field(
        default=5, ge=1, le=10, description="Hint: maximum number of source passages to retrieve."
    )


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    """Uniform error envelope for every non-2xx response."""

    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    schema_version: str = SCHEMA_VERSION
    handler: str


class UsageResponse(BaseModel):
    principal: str
    date_utc: str
    requests: int
    cost_usd: float
    daily_budget_usd: float
    remaining_budget_usd: float
