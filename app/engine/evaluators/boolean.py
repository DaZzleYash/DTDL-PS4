"""Boolean condition evaluator — owned by Contributor A."""

from typing import ClassVar

from app.engine.context import EvaluationContext
from app.engine.evaluators._helpers import (
    missing_field_explanation,
    require_keys,
    require_operator,
)
from app.engine.result import EvaluationResult
from app.exceptions import InvalidRuleError

OPERATORS = {"EQUALS", "NOT_EQUALS"}


class BooleanConditionEvaluator:
    type: ClassVar[str] = "BOOLEAN"

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        field = condition["field"]
        operator = condition["operator"]
        expected = condition["value"]
        actual = ctx.resolve_field(field)

        if actual is None:
            return EvaluationResult(False, missing_field_explanation(field))

        if not isinstance(actual, bool):
            return EvaluationResult(
                False,
                f"Field '{field}' value '{actual}' is not boolean — condition not matched",
            )

        matched = actual == expected if operator == "EQUALS" else actual != expected
        explanation = (
            f"{field} ({actual}) {operator} {expected} — "
            f"{'matched' if matched else 'not matched'}"
        )
        return EvaluationResult(matched, explanation)

    def validate(self, condition: dict) -> None:
        require_keys(condition, "type", "field", "operator", "value", type_label="BOOLEAN")
        if condition["type"] != self.type:
            raise InvalidRuleError(f"Expected type BOOLEAN, got '{condition['type']}'")
        require_operator(condition["operator"], OPERATORS, "BOOLEAN")
        if not isinstance(condition["value"], bool):
            raise InvalidRuleError("BOOLEAN condition 'value' must be a boolean")
