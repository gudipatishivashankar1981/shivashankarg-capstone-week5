"""Cost tracking for the EKA API.

Two cooperating pieces:

* :class:`CostTrackingMiddleware` - after each response, reads the ``cost_usd``
  the endpoint stored on ``request.state`` (taken from ``Answer.cost_usd``),
  adds it to the caller's running daily total and exposes it to the client in the
  ``X-Cost-USD`` response header.
* :class:`CostTracker` - thread-safe in-memory ledger keyed by (principal, UTC date)
  with a per-principal daily budget. The ``/ask`` route calls
  :meth:`CostTracker.check_budget` *before* doing any paid work, so a runaway
  client or evaluation loop cannot silently burn the budget.

Milestone 1 keeps the ledger in memory (resets on restart, not shared between
workers). ADR 0001 lists moving it to a shared store (Redis/Postgres) and wiring
it into FinOps dashboards as a follow-up. Floats are acceptable at this scale; use
Decimal if the ledger ever feeds billing.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

COST_HEADER = "X-Cost-USD"


class BudgetExceeded(Exception):
    """Raised when a principal has used up today's budget."""


@dataclass
class _Entry:
    requests: int = 0
    cost_usd: float = 0.0


def _utc_day(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")


class CostTracker:
    """In-memory, thread-safe daily cost ledger."""

    def __init__(self, daily_budget_usd: float = 25.0) -> None:
        if daily_budget_usd < 0:
            raise ValueError("daily_budget_usd must be >= 0")
        self.daily_budget_usd = daily_budget_usd
        self._lock = threading.Lock()
        self._ledger: dict[tuple[str, str], _Entry] = {}

    def record(self, principal: str, cost_usd: float, now: datetime | None = None) -> None:
        with self._lock:
            entry = self._ledger.setdefault((principal, _utc_day(now)), _Entry())
            entry.requests += 1
            entry.cost_usd += max(cost_usd, 0.0)

    def snapshot(self, principal: str, now: datetime | None = None) -> dict[str, float | int | str]:
        day = _utc_day(now)
        with self._lock:
            entry = self._ledger.get((principal, day), _Entry())
            spent, count = entry.cost_usd, entry.requests
        return {
            "principal": principal,
            "date_utc": day,
            "requests": count,
            "cost_usd": round(spent, 6),
            "daily_budget_usd": self.daily_budget_usd,
            "remaining_budget_usd": round(max(self.daily_budget_usd - spent, 0.0), 6),
        }

    def check_budget(self, principal: str, now: datetime | None = None) -> None:
        if self.snapshot(principal, now)["remaining_budget_usd"] <= 0:
            raise BudgetExceeded(principal)


class CostTrackingMiddleware(BaseHTTPMiddleware):
    """Records per-request cost and adds the ``X-Cost-USD`` header."""

    def __init__(self, app, tracker: CostTracker) -> None:  # noqa: ANN001
        super().__init__(app)
        self.tracker = tracker

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        cost = getattr(request.state, "cost_usd", None)  # set by the endpoint, if it did paid work
        if cost is not None:
            principal = getattr(request.state, "principal", "anonymous")
            self.tracker.record(principal, float(cost))
            response.headers[COST_HEADER] = f"{float(cost):.6f}"
        return response
