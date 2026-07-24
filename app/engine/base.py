"""Condition evaluator protocol — owned by Contributor A."""

from typing import ClassVar, Protocol

from app.engine.context import EvaluationContext
from app.engine.result import EvaluationResult


class ConditionEvaluator(Protocol):
    """Pluggable leaf-node evaluator for a single condition type."""

    type: ClassVar[str]

    def evaluate(self, condition: dict, ctx: EvaluationContext) -> EvaluationResult:
        """Evaluate the condition against the request context."""

    def validate(self, condition: dict) -> None:
        """Raise ``InvalidRuleError`` if the condition config is malformed."""
