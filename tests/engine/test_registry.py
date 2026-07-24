"""Tests for ConditionEvaluatorRegistry."""

import pytest

from app.engine.context import EvaluationContext
from app.engine.registry import ConditionEvaluatorRegistry
from app.exceptions import InvalidRuleError


@pytest.fixture
def registry() -> ConditionEvaluatorRegistry:
    return ConditionEvaluatorRegistry()


@pytest.fixture
def ctx() -> EvaluationContext:
    return EvaluationContext(
        {
            "applicant": {"creditScore": 720, "existingCustomer": True},
            "riskFlags": {"hasDefaulted": False},
        }
    )


def test_and_evaluates_all_children(registry: ConditionEvaluatorRegistry, ctx: EvaluationContext) -> None:
    condition = {
        "type": "AND",
        "conditions": [
            {
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
            {
                "type": "BOOLEAN",
                "field": "riskFlags.hasDefaulted",
                "operator": "EQUALS",
                "value": False,
            },
        ],
    }
    result = registry.evaluate(condition, ctx)
    assert result.matched is True
    assert "720" in result.explanation
    assert "hasDefaulted" in result.explanation


def test_and_not_matched_when_one_child_fails(
    registry: ConditionEvaluatorRegistry, ctx: EvaluationContext
) -> None:
    condition = {
        "type": "AND",
        "conditions": [
            {
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "LT",
                "value": 650,
            },
            {
                "type": "BOOLEAN",
                "field": "riskFlags.hasDefaulted",
                "operator": "EQUALS",
                "value": False,
            },
        ],
    }
    result = registry.evaluate(condition, ctx)
    assert result.matched is False


def test_or_matches_when_any_child_matches(
    registry: ConditionEvaluatorRegistry, ctx: EvaluationContext
) -> None:
    condition = {
        "type": "OR",
        "conditions": [
            {
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "LT",
                "value": 650,
            },
            {
                "type": "BOOLEAN",
                "field": "riskFlags.hasDefaulted",
                "operator": "EQUALS",
                "value": False,
            },
        ],
    }
    result = registry.evaluate(condition, ctx)
    assert result.matched is True


def test_not_inverts_child_result(registry: ConditionEvaluatorRegistry, ctx: EvaluationContext) -> None:
    condition = {
        "type": "NOT",
        "condition": {
            "type": "BOOLEAN",
            "field": "riskFlags.hasDefaulted",
            "operator": "EQUALS",
            "value": True,
        },
    }
    result = registry.evaluate(condition, ctx)
    assert result.matched is True


def test_nested_logical_conditions(registry: ConditionEvaluatorRegistry, ctx: EvaluationContext) -> None:
    condition = {
        "type": "AND",
        "conditions": [
            {
                "type": "OR",
                "conditions": [
                    {
                        "type": "NUMERIC",
                        "field": "applicant.creditScore",
                        "operator": "GTE",
                        "value": 700,
                    },
                    {
                        "type": "BOOLEAN",
                        "field": "applicant.existingCustomer",
                        "operator": "EQUALS",
                        "value": True,
                    },
                ],
            },
            {
                "type": "NOT",
                "condition": {
                    "type": "BOOLEAN",
                    "field": "riskFlags.hasDefaulted",
                    "operator": "EQUALS",
                    "value": True,
                },
            },
        ],
    }
    result = registry.evaluate(condition, ctx)
    assert result.matched is True


def test_unknown_type_raises(registry: ConditionEvaluatorRegistry, ctx: EvaluationContext) -> None:
    with pytest.raises(InvalidRuleError, match="Unknown condition type"):
        registry.evaluate({"type": "UNKNOWN"}, ctx)


def test_validate_unknown_type_raises(registry: ConditionEvaluatorRegistry) -> None:
    with pytest.raises(InvalidRuleError, match="Unknown condition type"):
        registry.validate({"type": "UNKNOWN"})


def test_validate_and_requires_children(registry: ConditionEvaluatorRegistry) -> None:
    with pytest.raises(InvalidRuleError, match="missing 'conditions'"):
        registry.validate({"type": "AND"})
