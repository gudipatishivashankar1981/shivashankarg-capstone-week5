"""Enterprise Knowledge Assistant (EKA) - FastAPI service skeleton (Milestone 1).

Run locally (from the project root)::

    export EKA_API_TOKENS="dev:change-me-please"
    uvicorn src.api.main:app --reload
    curl -s -X POST localhost:8000/ask \\
         -H "Authorization: Bearer change-me-please" -H "Content-Type: application/json" \\
         -d '{"question": "How many days of annual leave do employees receive?"}'

What is real in M1: the contract (``Answer`` schema v1), bearer-token auth, request
logging, cost tracking, uniform error envelope, budget guard.
What is a placeholder: the answer itself - :class:`PlaceholderHandler` always
returns a zero-confidence "please contact a human" response. Later milestones
replace the handler, not the API.

See docs/adr/0002-api-contract.md for the contract and its versioning rules.
"""

from __future__ import annotations

import hashlib
import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.auth import Principal, require_auth
from src.api.cost_tracking import BudgetExceeded, CostTracker, CostTrackingMiddleware
from src.api.logging_middleware import RequestLoggingMiddleware, configure_logging
from src.pipeline.handler import AnswerHandler, PlaceholderHandler
from src.pipeline.models import (
    SCHEMA_VERSION,
    Answer,
    AskRequest,
    ErrorResponse,
    HealthResponse,
    UsageResponse,
)

_log = logging.getLogger("eka.api")

_STATUS_CODES = {
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "rate_limited",
}


def _error(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
            "details": details,
        }
    }
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            code, message = exc.detail["code"], exc.detail.get("message", "")
        else:
            code = _STATUS_CODES.get(exc.status_code, "http_error")
            message = str(exc.detail)
        return _error(request, exc.status_code, code, message, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Never echo the submitted input back - questions may contain personal data.
        details = [
            {"field": ".".join(str(p) for p in err["loc"][1:]) or "body", "message": err["msg"]}
            for err in exc.errors()
        ]
        return _error(request, 422, "invalid_request", "Request body failed validation.", details=details)

    @app.exception_handler(Exception)
    async def _unhandled_exc(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        # The logging middleware has already logged the failure; do not leak internals.
        response = _error(request, 500, "internal_error", "An unexpected error occurred.")
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response


def _handler_from_env() -> AnswerHandler:
    """EKA_HANDLER=placeholder (default) or baseline (offline lexical demo; see baseline_handler.py)."""
    choice = os.getenv("EKA_HANDLER", "placeholder").strip().lower()
    if choice == "baseline":
        from src.pipeline.baseline_handler import BaselineHandler  # imported lazily: only needed on demand

        return BaselineHandler()
    if choice != "placeholder":
        raise ValueError(f"Unknown EKA_HANDLER '{choice}' (use 'placeholder' or 'baseline')")
    return PlaceholderHandler()


def create_app(handler: AnswerHandler | None = None, tracker: CostTracker | None = None) -> FastAPI:
    """Application factory. Handler and tracker are injectable for tests and later milestones."""
    configure_logging()

    app = FastAPI(
        title="Enterprise Knowledge Assistant API",
        version="0.1.0",
        description="Answers employee questions from approved internal documents, with sources and a "
        "confidence score, and escalates to a human when it cannot answer reliably.",
    )
    app.state.handler = handler or _handler_from_env()
    app.state.cost_tracker = tracker or CostTracker(float(os.getenv("EKA_DAILY_BUDGET_USD", "25")))

    # Middleware order: the LAST one added is the OUTERMOST. Logging wraps cost tracking
    # so the log line can include the cost that the inner middleware recorded.
    app.add_middleware(CostTrackingMiddleware, tracker=app.state.cost_tracker)
    app.add_middleware(RequestLoggingMiddleware)
    _register_exception_handlers(app)

    error_responses = {
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        422: {"model": ErrorResponse, "description": "Request body failed validation."},
        429: {"model": ErrorResponse, "description": "Daily cost budget exhausted."},
        500: {"model": ErrorResponse, "description": "Unexpected server error."},
    }

    @app.get("/health", response_model=HealthResponse, tags=["ops"])
    def health() -> HealthResponse:
        """Unauthenticated liveness probe."""
        return HealthResponse(status="ok", handler=app.state.handler.name)

    @app.post("/ask", response_model=Answer, responses=error_responses, tags=["assistant"])
    def ask(
        body: AskRequest,
        request: Request,
        response: Response,
        principal: Principal = Depends(require_auth),
    ) -> Answer:
        """Answer an employee question (contract: ADR 0002, schema v1)."""
        try:
            request.app.state.cost_tracker.check_budget(principal.name)
        except BudgetExceeded:
            raise HTTPException(
                status_code=429,
                detail={"code": "budget_exceeded", "message": "Daily cost budget exhausted for this caller."},
            ) from None

        # Privacy-safe breadcrumbs for the logging middleware (no question text by default).
        request.state.question_len = len(body.question)
        request.state.question_sha256 = hashlib.sha256(body.question.encode()).hexdigest()[:12]
        if os.getenv("EKA_LOG_QUESTIONS") == "1":  # local development only
            request.state.question_text = body.question

        answer = request.app.state.handler.answer(body.question, top_k=body.top_k)

        # Picked up by the cost-tracking and logging middleware.
        request.state.cost_usd = answer.cost_usd
        request.state.confidence = answer.confidence
        request.state.sources_count = len(answer.sources)
        request.state.retries = answer.retries

        response.headers["X-Schema-Version"] = answer.schema_version
        return answer

    @app.get("/usage", response_model=UsageResponse, responses=error_responses, tags=["ops"])
    def usage(request: Request, principal: Principal = Depends(require_auth)) -> UsageResponse:
        """Today's request count and spend for the calling principal."""
        return UsageResponse(**request.app.state.cost_tracker.snapshot(principal.name))

    return app


app = create_app()

__all__ = ["app", "create_app", "SCHEMA_VERSION"]
