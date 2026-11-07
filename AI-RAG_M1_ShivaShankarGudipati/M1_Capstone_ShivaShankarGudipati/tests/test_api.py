"""Unit tests for the FastAPI skeleton: auth, logging, cost tracking, placeholder handler."""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from src.api.auth import authenticate, load_tokens
from src.api.cost_tracking import CostTracker
from src.api.main import create_app
from src.pipeline.models import ESCALATION_THRESHOLD, Answer

ALICE = {"Authorization": "Bearer tok-alice-123"}
BOB = {"Authorization": "Bearer tok-bob-456"}
Q = {"question": "How many days of annual leave do employees receive?"}


class FixedCostHandler:
    """Stand-in for the future RAG handler: confident, cited, and costs money."""

    name = "fixed-cost"

    def __init__(self, cost: float = 0.0123):
        self.cost = cost

    def answer(self, question: str, *, top_k: int = 5) -> Answer:
        return Answer(content="20 working days.", cost_usd=self.cost, retries=1, confidence=0.93, sources=["HR-001#2.1"])


class ExplodingHandler:
    name = "exploding"

    def answer(self, question: str, *, top_k: int = 5) -> Answer:
        raise RuntimeError("secret internal detail: db password is hunter2")


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    monkeypatch.setenv("EKA_API_TOKENS", "alice:tok-alice-123,bob:tok-bob-456")
    monkeypatch.delenv("EKA_LOG_QUESTIONS", raising=False)
    monkeypatch.delenv("EKA_HANDLER", raising=False)


@pytest.fixture
def client():
    return TestClient(create_app())


# ---------------------------------------------------------------- health / auth
def test_health_is_public(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "schema_version": "v1", "handler": "placeholder"}


def test_ask_requires_token(client):
    r = client.post("/ask", json=Q)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["error"]["code"] == "unauthorized"


@pytest.mark.parametrize("header", ["Bearer wrong-token", "Basic tok-alice-123", "Bearer ", "tok-alice-123"])
def test_ask_rejects_bad_credentials(client, header):
    r = client.post("/ask", json=Q, headers={"Authorization": header})
    assert r.status_code == 401
    assert "tok-alice-123" not in r.text


def test_fail_closed_when_no_tokens_configured(monkeypatch):
    monkeypatch.delenv("EKA_API_TOKENS")
    r = TestClient(create_app()).post("/ask", json=Q, headers=ALICE)
    assert r.status_code == 401


def test_token_parsing_and_matching():
    tokens = load_tokens({"EKA_API_TOKENS": " a:one , b:two:with-colon, bare-token ,"})
    assert tokens["a"] == "one" and tokens["b"] == "two:with-colon"
    assert any(name.startswith("token-") and tok == "bare-token" for name, tok in tokens.items())
    assert authenticate("two:with-colon", tokens) == "b"
    assert authenticate("nope", tokens) is None


# ---------------------------------------------------------------- /ask + placeholder
def test_ask_returns_valid_v1_placeholder_answer(client):
    r = client.post("/ask", json=Q, headers=ALICE)
    assert r.status_code == 200
    answer = Answer.model_validate(r.json())  # response conforms to the contract
    assert answer.schema_version == "v1"
    assert answer.content.startswith("[PLACEHOLDER]")
    assert answer.sources == [] and answer.cost_usd == 0.0 and answer.retries == 0
    assert answer.confidence < ESCALATION_THRESHOLD and answer.needs_escalation()
    assert r.headers["x-schema-version"] == "v1"


@pytest.mark.parametrize(
    "payload",
    [{}, {"question": ""}, {"question": "  "}, {"question": "x" * 2001}, {"question": "valid question", "top_k": 99}, {"q": "typo"}],
)
def test_ask_validation_errors_use_error_envelope(client, payload):
    r = client.post("/ask", json=payload, headers=ALICE)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "invalid_request" and err["details"]
    assert err["request_id"] == r.headers["x-request-id"]


def test_validation_errors_do_not_echo_input(client):
    secret = "my-national-id-1234567890 " * 100  # too long -> 422
    r = client.post("/ask", json={"question": secret}, headers=ALICE)
    assert r.status_code == 422 and "1234567890" not in r.text


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_unhandled_error_is_masked(monkeypatch):
    c = TestClient(create_app(handler=ExplodingHandler()), raise_server_exceptions=False)
    r = c.post("/ask", json=Q, headers=ALICE)
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in r.text
    assert r.headers["x-request-id"] == r.json()["error"]["request_id"]


# ---------------------------------------------------------------- logging middleware
def test_request_id_is_generated_and_echoed(client):
    generated = client.get("/health").headers["x-request-id"]
    assert len(generated) == 32
    r = client.get("/health", headers={"X-Request-ID": "trace-abc-12345"})
    assert r.headers["x-request-id"] == "trace-abc-12345"
    r = client.get("/health", headers={"X-Request-ID": "bad id with spaces!"})  # unsafe -> replaced
    assert r.headers["x-request-id"] != "bad id with spaces!"


def test_request_log_has_fields_and_never_logs_question_or_token(client, caplog):
    with caplog.at_level(logging.INFO, logger="eka.request"):
        client.post("/ask", json=Q, headers=ALICE)
    rec = next(r for r in caplog.records if r.name == "eka.request")
    fields = rec.eka
    assert fields["method"] == "POST" and fields["path"] == "/ask" and fields["status"] == 200
    assert fields["principal"] == "alice" and fields["latency_ms"] >= 0
    assert fields["question_len"] == len(Q["question"]) and len(fields["question_sha256"]) == 12
    assert fields["confidence"] == 0.0 and fields["sources_count"] == 0
    blob = json.dumps(fields)
    assert "annual leave" not in blob and "tok-alice-123" not in blob and "question_text" not in fields


def test_question_text_logged_only_when_explicitly_enabled(monkeypatch, caplog):
    monkeypatch.setenv("EKA_LOG_QUESTIONS", "1")
    with caplog.at_level(logging.INFO, logger="eka.request"):
        TestClient(create_app()).post("/ask", json=Q, headers=ALICE)
    rec = next(r for r in caplog.records if r.name == "eka.request")
    assert rec.eka["question_text"] == Q["question"]


def test_unauthenticated_request_is_logged_as_anonymous(client, caplog):
    with caplog.at_level(logging.INFO, logger="eka.request"):
        client.post("/ask", json=Q)
    rec = next(r for r in caplog.records if r.name == "eka.request")
    assert rec.eka["principal"] == "anonymous" and rec.eka["status"] == 401


# ---------------------------------------------------------------- cost tracking
def test_cost_header_and_usage_endpoint():
    tracker = CostTracker(daily_budget_usd=1.0)
    c = TestClient(create_app(handler=FixedCostHandler(0.0123), tracker=tracker))
    r1 = c.post("/ask", json=Q, headers=ALICE)
    r2 = c.post("/ask", json=Q, headers=ALICE)
    assert r1.headers["x-cost-usd"] == "0.012300"
    c.post("/ask", json=Q, headers=BOB)

    usage = c.get("/usage", headers=ALICE).json()
    assert usage["principal"] == "alice" and usage["requests"] == 2
    assert usage["cost_usd"] == pytest.approx(0.0246)
    assert usage["remaining_budget_usd"] == pytest.approx(1.0 - 0.0246)
    assert c.get("/usage", headers=BOB).json()["requests"] == 1  # per-principal isolation
    assert r2.status_code == 200


def test_placeholder_costs_nothing(client):
    r = client.post("/ask", json=Q, headers=ALICE)
    assert r.headers["x-cost-usd"] == "0.000000"
    assert client.get("/usage", headers=ALICE).json()["cost_usd"] == 0.0


def test_failed_requests_are_not_billed(client):
    client.post("/ask", json=Q)  # 401
    client.post("/ask", json={}, headers=ALICE)  # 422
    assert client.get("/usage", headers=ALICE).json()["requests"] == 0


def test_daily_budget_is_enforced():
    tracker = CostTracker(daily_budget_usd=0.02)
    c = TestClient(create_app(handler=FixedCostHandler(0.015), tracker=tracker))
    assert c.post("/ask", json=Q, headers=ALICE).status_code == 200  # 0.015 spent
    assert c.post("/ask", json=Q, headers=ALICE).status_code == 200  # 0.030 spent (budget now exceeded)
    r = c.post("/ask", json=Q, headers=ALICE)
    assert r.status_code == 429 and r.json()["error"]["code"] == "budget_exceeded"
    assert c.post("/ask", json=Q, headers=BOB).status_code == 200  # other principals unaffected


def test_tracker_unit_behaviour():
    t = CostTracker(daily_budget_usd=0.01)
    t.record("p", 0.004)
    t.record("p", -5)  # negative costs are ignored, never credit the ledger
    snap = t.snapshot("p")
    assert snap["requests"] == 2 and snap["cost_usd"] == pytest.approx(0.004)
    t.check_budget("p")
    t.record("p", 0.01)
    with pytest.raises(Exception):
        t.check_budget("p")
    with pytest.raises(ValueError):
        CostTracker(-1)
