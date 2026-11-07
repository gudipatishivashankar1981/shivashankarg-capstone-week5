"""Bearer-token authentication for the EKA API.

Tokens come from the ``EKA_API_TOKENS`` environment variable as comma-separated
``name:token`` pairs, e.g. ``EKA_API_TOKENS="portal:s3cr3t-1,evalbot:s3cr3t-2"``.
The *name* becomes the caller's principal (used for logging and cost
attribution); the token itself is never logged.

Design choices:
  * Fail closed: if no tokens are configured, every protected call gets 401.
  * Constant-time comparison (``hmac.compare_digest``) against every configured token.
  * No default/dev token is baked into the code.
  * Milestone 1 uses static service tokens. ADR 0002 records the planned move to
    SSO-issued JWTs with per-user identity and document-level access control.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

TOKENS_ENV = "EKA_API_TOKENS"

_bearer = HTTPBearer(auto_error=False)
_log = logging.getLogger("eka.auth")


@dataclass(frozen=True)
class Principal:
    """The authenticated caller."""

    name: str


def load_tokens(environ: dict[str, str] | None = None) -> dict[str, str]:
    """Parse ``EKA_API_TOKENS`` into ``{principal_name: token}``."""
    raw = (environ if environ is not None else os.environ).get(TOKENS_ENV, "")
    tokens: dict[str, str] = {}
    for item in (part.strip() for part in raw.split(",")):
        if not item:
            continue
        if ":" in item:
            name, token = item.split(":", 1)
            name, token = name.strip(), token.strip()
        else:  # bare token: derive a stable, non-reversible principal name
            token = item
            name = "token-" + hashlib.sha256(token.encode()).hexdigest()[:8]
        if name and token:
            tokens[name] = token
    return tokens


def authenticate(presented: str, tokens: dict[str, str]) -> str | None:
    """Return the principal name for a valid token, else ``None`` (constant time)."""
    matched: str | None = None
    for name, token in tokens.items():
        if hmac.compare_digest(presented.encode(), token.encode()):
            matched = name
    return matched


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    """FastAPI dependency: validates ``Authorization: Bearer <token>``."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise _unauthorized("Missing or malformed bearer token.")

    tokens = load_tokens()
    if not tokens:
        _log.error("No API tokens configured (%s is empty); rejecting all protected requests.", TOKENS_ENV)
        raise _unauthorized("Invalid bearer token.")

    name = authenticate(credentials.credentials, tokens)
    if name is None:
        raise _unauthorized("Invalid bearer token.")

    request.state.principal = name  # picked up by logging and cost-tracking middleware
    return Principal(name=name)
