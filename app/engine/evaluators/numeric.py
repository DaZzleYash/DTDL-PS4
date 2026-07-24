"""Numeric condition evaluator — owned by Contributor A."""

from typing import ClassVar

from app.engine.context import EvaluationContext
from app.engine.evaluators._helpers import (
    missing_field_explanation,
    require_keys,
    require_operator,
)
from app.engine.result import EvaluationResult
from app.exceptions import InvalidRuleError

OPERATORS = {"EQUALS", "NOT_EQUALS", "GT", "GTE", "LT", "LTE"}


class NumericConditionEvaluator:
    type: ClassVar[str] = "NUMERIC"

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        field = condition["field"]
        operator = condition["operator"]
        expected = condition["value"]
        actual = ctx.resolve_field(field)

        if actual is None:
            return EvaluationResult(False, missing_field_explanation(field))

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError):
            return EvaluationResult(
                False,
                f"Field '{field}' value '{actual}' is not numeric — condition not matched",
            )

        matched = _compare(actual_num, expected_num, operator)
        symbol = _operator_symbol(operator)
        explanation = (
            f"{field} ({actual_num}) {symbol} {expected_num} — "
            f"{'matched' if matched else 'not matched'}"
        )
        return EvaluationResult(matched, explanation)

    def validate(self, condition: dict) -> None:
        require_keys(condition, "type", "field", "operator", "value", type_label="NUMERIC")
        if condition["type"] != self.type:
            raise InvalidRuleError(f"Expected type NUMERIC, got '{condition['type']}'")
        require_operator(condition["operator"], OPERATORS, "NUMERIC")
        try:
            float(condition["value"])
        except (TypeError, ValueError) as exc:
            raise InvalidRuleError("NUMERIC condition 'value' must be a number") from exc


def _compare(actual: float, expected: float, operator: str) -> bool:
    if operator == "EQUALS":
        return actual == expected
    if operator == "NOT_EQUALS":
        return actual != expected
    if operator == "GT":
        return actual > expected
    if operator == "GTE":
        return actual >= expected
    if operator == "LT":
        return actual < expected
    if operator == "LTE":
        return actual <= expected
    return False


def _operator_symbol(operator: str) -> str:
    return {
        "EQUALS": "==",
        "NOT_EQUALS": "!=",
        "GT": ">",
        "GTE": ">=",
        "LT": "<",
        "LTE": "<=",
    }[operator]
