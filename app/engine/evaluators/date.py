"""Date condition evaluator — owned by Contributor A."""

from datetime import date, datetime
from typing import ClassVar

from app.engine.context import EvaluationContext
from app.engine.evaluators._helpers import (
    missing_field_explanation,
    require_keys,
    require_operator,
)
from app.engine.result import EvaluationResult
from app.exceptions import InvalidRuleError

OPERATORS = {"BEFORE", "AFTER", "EQUALS", "ON_OR_BEFORE", "ON_OR_AFTER"}


class DateConditionEvaluator:
    type: ClassVar[str] = "DATE"

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        field = condition["field"]
        operator = condition["operator"]
        expected_raw = condition["value"]
        actual = ctx.resolve_field(field)

        if actual is None:
            return EvaluationResult(False, missing_field_explanation(field))

        try:
            actual_date = _parse_date(actual)
            expected_date = _parse_date(expected_raw)
        except ValueError:
            return EvaluationResult(
                False,
                f"Field '{field}' or expected value is not a valid ISO-8601 date — not matched",
            )

        matched = _compare(actual_date, expected_date, operator)
        explanation = (
            f"{field} ({actual_date.isoformat()}) {operator} {expected_date.isoformat()} — "
            f"{'matched' if matched else 'not matched'}"
        )
        return EvaluationResult(matched, explanation)

    def validate(self, condition: dict) -> None:
        require_keys(condition, "type", "field", "operator", "value", type_label="DATE")
        if condition["type"] != self.type:
            raise InvalidRuleError(f"Expected type DATE, got '{condition['type']}'")
        require_operator(condition["operator"], OPERATORS, "DATE")
        try:
            _parse_date(condition["value"])
        except ValueError as exc:
            raise InvalidRuleError("DATE condition 'value' must be a valid ISO-8601 date") from exc


def _parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        raise ValueError("unsupported date value")
    normalized = value.replace("Z", "+00:00")
    if "T" in normalized:
        return datetime.fromisoformat(normalized).date()
    return date.fromisoformat(normalized)


def _compare(actual: date, expected: date, operator: str) -> bool:
    if operator == "BEFORE":
        return actual < expected
    if operator == "AFTER":
        return actual > expected
    if operator == "EQUALS":
        return actual == expected
    if operator == "ON_OR_BEFORE":
        return actual <= expected
    if operator == "ON_OR_AFTER":
        return actual >= expected
    return False
