"""Tests for EvaluationContext."""

from app.engine.context import EvaluationContext


def test_resolve_field_returns_nested_value() -> None:
    ctx = EvaluationContext({"applicant": {"creditScore": 720}})
    assert ctx.resolve_field("applicant.creditScore") == 720


def test_resolve_field_returns_none_for_missing_path() -> None:
    ctx = EvaluationContext({"applicant": {}})
    assert ctx.resolve_field("applicant.creditScore") is None


def test_resolve_field_returns_none_for_missing_intermediate() -> None:
    ctx = EvaluationContext({})
    assert ctx.resolve_field("applicant.creditScore") is None
