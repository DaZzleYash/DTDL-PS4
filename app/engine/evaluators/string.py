"""String condition evaluator — owned by Contributor A."""

from typing import ClassVar

from app.engine.context import EvaluationContext
from app.engine.evaluators._helpers import (
    missing_field_explanation,
    require_keys,
    require_operator,
)
from app.engine.result import EvaluationResult
from app.exceptions import InvalidRuleError

OPERATORS = {"EQUALS", "NOT_EQUALS", "CONTAINS", "STARTS_WITH", "ENDS_WITH", "IN", "NOT_IN"}


class StringConditionEvaluator:
    type: ClassVar[str] = "STRING"

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        field = condition["field"]
        operator = condition["operator"]
        expected = condition["value"]
        actual = ctx.resolve_field(field)

        if actual is None:
            return EvaluationResult(False, missing_field_explanation(field))

        actual_str = str(actual)
        expected_str = str(expected)
        matched = _compare(actual_str, expected, operator)
        explanation = (
            f"{field} ('{actual_str}') {operator} '{expected_str}' — "
            f"{'matched' if matched else 'not matched'}"
        )
        return EvaluationResult(matched, explanation)

    def validate(self, condition: dict) -> None:
        require_keys(condition, "type", "field", "operator", "value", type_label="STRING")
        if condition["type"] != self.type:
            raise InvalidRuleError(f"Expected type STRING, got '{condition['type']}'")
        require_operator(condition["operator"], OPERATORS, "STRING")
        operator = condition["operator"]
        if operator in {"IN", "NOT_IN"} and not isinstance(condition["value"], list):
            raise InvalidRuleError("STRING condition 'value' must be a list for IN/NOT_IN operators")


def _compare(actual: str, expected: object, operator: str) -> bool:
    if operator == "EQUALS":
        return actual == str(expected)
    if operator == "NOT_EQUALS":
        return actual != str(expected)
    if operator == "CONTAINS":
        return str(expected) in actual
    if operator == "STARTS_WITH":
        return actual.startswith(str(expected))
    if operator == "ENDS_WITH":
        return actual.endswith(str(expected))
    if operator == "IN":
        return actual in [str(item) for item in expected]  # type: ignore[union-attr]
    if operator == "NOT_IN":
        return actual not in [str(item) for item in expected]  # type: ignore[union-attr]
    return False
