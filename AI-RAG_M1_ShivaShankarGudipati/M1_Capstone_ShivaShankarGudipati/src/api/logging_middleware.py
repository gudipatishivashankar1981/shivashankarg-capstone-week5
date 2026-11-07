"""Request logging middleware for the EKA API.

Emits one structured (JSON) log line per request with: request id, method, path,
status, latency, principal, and - when the endpoint recorded them - question
length, a short hash of the question, answer confidence, source count, retries
and cost.

Privacy by default: the *text* of the employee's question is NOT logged, because
questions can contain personal data. Set ``EKA_LOG_QUESTIONS=1`` in local
development only to include it. Bearer tokens and query strings are never logged.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

logger = logging.getLogger("eka.request")

# Attributes the endpoint may set on ``request.state`` for inclusion in the log line.
_OPTIONAL_STATE_FIELDS = (
    "question_len",
    "question_sha256",
    "question_text",
    "confidence",
    "sources_count",
    "retries",
    "cost_usd",
)


class JsonLogFormatter(logging.Formatter):
    """Formats log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "eka", {}))
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Install a JSON handler on the ``eka`` logger (idempotent)."""
    eka_logger = logging.getLogger("eka")
    eka_logger.setLevel(level)
    if not any(getattr(h, "_eka_json", False) for h in eka_logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        handler._eka_json = True  # type: ignore[attr-defined]
        eka_logger.addHandler(handler)


def _request_id_from(request: Request) -> str:
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    return incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assigns a request id, times the request and logs one line when it ends."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _request_id_from(request)
        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            self._log(request, request_id, started, status_code=500, level=logging.ERROR, exc_info=True)
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        self._log(request, request_id, started, status_code=response.status_code, level=logging.INFO)
        return response

    @staticmethod
    def _log(
        request: Request,
        request_id: str,
        started: float,
        *,
        status_code: int,
        level: int,
        exc_info: bool = False,
    ) -> None:
        fields: dict[str, object] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,  # no query string
            "status": status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "principal": getattr(request.state, "principal", "anonymous"),
        }
        for name in _OPTIONAL_STATE_FIELDS:
            value = getattr(request.state, name, None)
            if value is not None:
                fields[name] = value
        logger.log(level, "request", extra={"eka": fields}, exc_info=exc_info)
