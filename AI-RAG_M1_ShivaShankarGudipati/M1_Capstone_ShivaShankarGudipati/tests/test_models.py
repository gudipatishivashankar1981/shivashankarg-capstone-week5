"""Contract tests for the v1 Answer schema (ADR 0002)."""

import pytest
from pydantic import ValidationError

from src.pipeline.models import ESCALATION_THRESHOLD, Answer, AskRequest

V1_FIELDS = {"content", "cost_usd", "retries", "confidence", "sources", "schema_version"}


def make(**overrides):
    data = dict(content="Employees receive 20 working days.", cost_usd=0.002, retries=0, confidence=0.9, sources=["HR-001"])
    data.update(overrides)
    return Answer(**data)


def test_v1_field_set_is_frozen():
    """Adding/removing/renaming a v1 field must fail this test (breaking change => v2)."""
    assert set(Answer.model_fields) == V1_FIELDS
    assert set(make().model_dump()) == V1_FIELDS


def test_schema_version_defaults_to_v1():
    assert make().schema_version == "v1"


def test_field_types_match_contract():
    fields = Answer.model_fields
    assert fields["content"].annotation is str
    assert fields["cost_usd"].annotation is float
    assert fields["retries"].annotation is int
    assert fields["confidence"].annotation is float
    assert fields["sources"].annotation == list[str]


@pytest.mark.parametrize("missing", ["content", "cost_usd", "retries", "confidence", "sources"])
def test_required_fields(missing):
    data = dict(content="x", cost_usd=0.0, retries=0, confidence=0.5, sources=[])
    data.pop(missing)
    with pytest.raises(ValidationError):
        Answer(**data)


@pytest.mark.parametrize("bad", [dict(confidence=1.01), dict(confidence=-0.1), dict(cost_usd=-0.01), dict(retries=-1)])
def test_range_validation(bad):
    with pytest.raises(ValidationError):
        make(**bad)


def test_unknown_fields_rejected_server_side():
    with pytest.raises(ValidationError):
        make(unexpected="field")


def test_escalation_convention():
    assert make(confidence=ESCALATION_THRESHOLD - 0.01).needs_escalation()
    assert not make(confidence=ESCALATION_THRESHOLD).needs_escalation()


def test_json_round_trip():
    original = make(sources=["HR-001#2.1", "HR-004"])
    assert Answer.model_validate_json(original.model_dump_json()) == original


def test_ask_request_strips_and_validates():
    assert AskRequest(question="  How many leave days?  ").question == "How many leave days?"
    with pytest.raises(ValidationError):
        AskRequest(question="  ")
    with pytest.raises(ValidationError):
        AskRequest(question="x" * 2001)
    with pytest.raises(ValidationError):
        AskRequest(question="valid question", top_k=0)
