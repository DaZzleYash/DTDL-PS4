"""Unit tests for leaf condition evaluators."""

import pytest

from app.engine.context import EvaluationContext
from app.engine.evaluators.boolean import BooleanConditionEvaluator
from app.engine.evaluators.date import DateConditionEvaluator
from app.engine.evaluators.numeric import NumericConditionEvaluator
from app.engine.evaluators.string import StringConditionEvaluator
from app.exceptions import InvalidRuleError


@pytest.fixture
def ctx() -> EvaluationContext:
    return EvaluationContext(
        {
            "applicant": {
                "creditScore": 720,
                "employmentStatus": "EMPLOYED",
                "dateOfBirth": "1990-05-15",
            },
            "riskFlags": {"hasDefaulted": False},
        }
    )


class TestNumericConditionEvaluator:
    evaluator = NumericConditionEvaluator()

    def test_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "NUMERIC",
            "field": "applicant.creditScore",
            "operator": "GTE",
            "value": 650,
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is True

    def test_non_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "NUMERIC",
            "field": "applicant.creditScore",
            "operator": "LT",
            "value": 650,
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is False

    def test_missing_field(self) -> None:
        condition = {
            "type": "NUMERIC",
            "field": "applicant.missing",
            "operator": "GTE",
            "value": 650,
        }
        result = self.evaluator.evaluate(condition, EvaluationContext({}))
        assert result.matched is False

    def test_invalid_config(self) -> None:
        with pytest.raises(InvalidRuleError, match="unsupported operator"):
            self.evaluator.validate(
                {
                    "type": "NUMERIC",
                    "field": "applicant.creditScore",
                    "operator": "CONTAINS",
                    "value": 650,
                }
            )


class TestStringConditionEvaluator:
    evaluator = StringConditionEvaluator()

    def test_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "STRING",
            "field": "applicant.employmentStatus",
            "operator": "EQUALS",
            "value": "EMPLOYED",
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is True

    def test_non_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "STRING",
            "field": "applicant.employmentStatus",
            "operator": "EQUALS",
            "value": "UNEMPLOYED",
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is False

    def test_missing_field(self) -> None:
        condition = {
            "type": "STRING",
            "field": "applicant.employmentStatus",
            "operator": "EQUALS",
            "value": "EMPLOYED",
        }
        result = self.evaluator.evaluate(condition, EvaluationContext({}))
        assert result.matched is False

    def test_invalid_config(self) -> None:
        with pytest.raises(InvalidRuleError, match="must be a list"):
            self.evaluator.validate(
                {
                    "type": "STRING",
                    "field": "applicant.employmentStatus",
                    "operator": "IN",
                    "value": "EMPLOYED",
                }
            )


class TestBooleanConditionEvaluator:
    evaluator = BooleanConditionEvaluator()

    def test_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "BOOLEAN",
            "field": "riskFlags.hasDefaulted",
            "operator": "EQUALS",
            "value": False,
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is True

    def test_non_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "BOOLEAN",
            "field": "riskFlags.hasDefaulted",
            "operator": "EQUALS",
            "value": True,
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is False

    def test_missing_field(self) -> None:
        condition = {
            "type": "BOOLEAN",
            "field": "riskFlags.hasDefaulted",
            "operator": "EQUALS",
            "value": False,
        }
        result = self.evaluator.evaluate(condition, EvaluationContext({}))
        assert result.matched is False

    def test_invalid_config(self) -> None:
        with pytest.raises(InvalidRuleError, match="must be a boolean"):
            self.evaluator.validate(
                {
                    "type": "BOOLEAN",
                    "field": "riskFlags.hasDefaulted",
                    "operator": "EQUALS",
                    "value": "false",
                }
            )


class TestDateConditionEvaluator:
    evaluator = DateConditionEvaluator()

    def test_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "DATE",
            "field": "applicant.dateOfBirth",
            "operator": "BEFORE",
            "value": "2000-01-01",
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is True

    def test_non_matching(self, ctx: EvaluationContext) -> None:
        condition = {
            "type": "DATE",
            "field": "applicant.dateOfBirth",
            "operator": "AFTER",
            "value": "2000-01-01",
        }
        result = self.evaluator.evaluate(condition, ctx)
        assert result.matched is False

    def test_missing_field(self) -> None:
        condition = {
            "type": "DATE",
            "field": "applicant.dateOfBirth",
            "operator": "BEFORE",
            "value": "2000-01-01",
        }
        result = self.evaluator.evaluate(condition, EvaluationContext({}))
        assert result.matched is False

    def test_invalid_config(self) -> None:
        with pytest.raises(InvalidRuleError, match="valid ISO-8601"):
            self.evaluator.validate(
                {
                    "type": "DATE",
                    "field": "applicant.dateOfBirth",
                    "operator": "BEFORE",
                    "value": "not-a-date",
                }
            )
