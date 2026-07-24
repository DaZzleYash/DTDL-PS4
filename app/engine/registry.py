"""Condition evaluator registry — owned by Contributor A."""

from app.engine.base import ConditionEvaluator
from app.engine.context import EvaluationContext
from app.engine.evaluators.boolean import BooleanConditionEvaluator
from app.engine.evaluators.date import DateConditionEvaluator
from app.engine.evaluators.numeric import NumericConditionEvaluator
from app.engine.evaluators.string import StringConditionEvaluator
from app.engine.result import EvaluationResult
from app.exceptions import InvalidRuleError

LOGICAL_TYPES = {"AND", "OR", "NOT"}

EVALUATORS: list[ConditionEvaluator] = [
    NumericConditionEvaluator(),
    StringConditionEvaluator(),
    BooleanConditionEvaluator(),
    DateConditionEvaluator(),
]


class ConditionEvaluatorRegistry:
    """Dispatches condition JSON trees to registered leaf evaluators."""

    def __init__(self, evaluators: list[ConditionEvaluator] | None = None) -> None:
        self._evaluators = evaluators if evaluators is not None else EVALUATORS
        self._by_type = {evaluator.type: evaluator for evaluator in self._evaluators}

    @property
    def supported_types(self) -> list[str]:
        return sorted({*self._by_type.keys(), *LOGICAL_TYPES})

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        condition_type = condition.get("type")
        if condition_type in LOGICAL_TYPES:
            return self._evaluate_logical(condition, ctx)
        evaluator = self._by_type.get(condition_type)  # type: ignore[arg-type]
        if evaluator is None:
            raise InvalidRuleError(
                f"Unknown condition type '{condition_type}'. "
                f"Supported types: {', '.join(self.supported_types)}"
            )
        return evaluator.evaluate(condition, ctx)

    def validate(self, condition: dict) -> None:
        if not isinstance(condition, dict):
            raise InvalidRuleError("Condition must be a JSON object")
        condition_type = condition.get("type")
        if condition_type in LOGICAL_TYPES:
            self._validate_logical(condition)
            return
        evaluator = self._by_type.get(condition_type)  # type: ignore[arg-type]
        if evaluator is None:
            raise InvalidRuleError(
                f"Unknown condition type '{condition_type}'. "
                f"Supported types: {', '.join(self.supported_types)}"
            )
        evaluator.validate(condition)

    def _evaluate_logical(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        condition_type = condition["type"]

        if condition_type == "AND":
            children = condition["conditions"]
            results = [self.evaluate(child, ctx) for child in children]
            matched = all(result.matched for result in results)
            child_explanations = "; ".join(result.explanation for result in results)
            explanation = f"AND ({len(results)} conditions) — {child_explanations} — {'matched' if matched else 'not matched'}"
            return EvaluationResult(matched, explanation)

        if condition_type == "OR":
            children = condition["conditions"]
            results = [self.evaluate(child, ctx) for child in children]
            matched = any(result.matched for result in results)
            child_explanations = "; ".join(result.explanation for result in results)
            explanation = f"OR ({len(results)} conditions) — {child_explanations} — {'matched' if matched else 'not matched'}"
            return EvaluationResult(matched, explanation)

        child = condition["condition"]
        result = self.evaluate(child, ctx)
        matched = not result.matched
        explanation = f"NOT — {result.explanation} — {'matched' if matched else 'not matched'}"
        return EvaluationResult(matched, explanation)

    def _validate_logical(self, condition: dict) -> None:
        condition_type = condition.get("type")
        if condition_type not in LOGICAL_TYPES:
            raise InvalidRuleError(f"Expected logical type, got '{condition_type}'")

        if condition_type in {"AND", "OR"}:
            if "conditions" not in condition:
                raise InvalidRuleError(f"{condition_type} condition missing 'conditions' list")
            if not isinstance(condition["conditions"], list):
                raise InvalidRuleError(f"{condition_type} condition 'conditions' must be a list")
            if not condition["conditions"]:
                raise InvalidRuleError(f"{condition_type} condition must have at least one child")
            for child in condition["conditions"]:
                if not isinstance(child, dict):
                    raise InvalidRuleError(f"{condition_type} child conditions must be objects")
                self.validate(child)
            return

        if "condition" not in condition:
            raise InvalidRuleError("NOT condition missing 'condition'")
        if not isinstance(condition["condition"], dict):
            raise InvalidRuleError("NOT condition 'condition' must be an object")
        self.validate(condition["condition"])
