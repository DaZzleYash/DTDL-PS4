"""Decision evaluation algorithm — owned by Contributor C."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.engine.context import EvaluationContext
from app.engine.registry import ConditionEvaluatorRegistry
from app.exceptions import InvalidRuleError
from app.rules.repository import RuleRepository
from app.schemas.decision import DecisionResponse, EvaluateRequest, RuleTrace

logger = logging.getLogger(__name__)


class DecisionEngineService:
    """Evaluates active rules against a request context and returns an explainable decision."""

    def __init__(
        self,
        repository: RuleRepository,
        registry: ConditionEvaluatorRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry or ConditionEvaluatorRegistry()

    def evaluate(self, request: EvaluateRequest) -> DecisionResponse:
        rules = self._repository.list_active_ordered_by_priority(category=request.category)
        ctx = EvaluationContext(request.context)

        rules_evaluated: list[RuleTrace] = []
        rules_matched: list[RuleTrace] = []
        rules_rejected: list[RuleTrace] = []

        for rule in rules:
            trace = self._evaluate_rule(rule, ctx)
            rules_evaluated.append(trace)
            if trace.matched:
                rules_matched.append(trace)
            else:
                rules_rejected.append(trace)

        matched_decisions = list(dict.fromkeys(trace.decision_outcome for trace in rules_matched))
        final_decision = rules_matched[0].decision_outcome if rules_matched else "NO_DECISION"
        explanation = self._build_explanation(
            final_decision=final_decision,
            rules_evaluated=rules_evaluated,
            rules_matched=rules_matched,
        )

        return DecisionResponse(
            final_decision=final_decision,
            matched_decisions=matched_decisions,
            explanation=explanation,
            rules_evaluated=rules_evaluated,
            rules_matched=rules_matched,
            rules_rejected=rules_rejected,
            evaluated_at=datetime.now(UTC),
        )

    def evaluate_bulk(self, requests: list[EvaluateRequest]) -> list[DecisionResponse]:
        return [self.evaluate(request) for request in requests]

    def _evaluate_rule(self, rule, ctx: EvaluationContext) -> RuleTrace:
        try:
            condition = json.loads(rule.condition_json)
        except json.JSONDecodeError as exc:
            explanation = f"Skipped: stored condition is invalid JSON ({exc.msg})"
            logger.warning("Rule %s (%s) skipped: invalid JSON", rule.id, rule.name)
            return RuleTrace(
                rule_id=rule.id,
                rule_name=rule.name,
                priority=rule.priority,
                matched=False,
                decision_outcome=None,
                explanation=explanation,
            )

        try:
            result = self._registry.evaluate(condition, ctx)
        except InvalidRuleError as exc:
            explanation = f"Skipped: {exc.message}"
            logger.warning("Rule %s (%s) skipped: %s", rule.id, rule.name, exc.message)
            return RuleTrace(
                rule_id=rule.id,
                rule_name=rule.name,
                priority=rule.priority,
                matched=False,
                decision_outcome=None,
                explanation=explanation,
            )

        return RuleTrace(
            rule_id=rule.id,
            rule_name=rule.name,
            priority=rule.priority,
            matched=result.matched,
            decision_outcome=rule.decision_outcome if result.matched else None,
            explanation=result.explanation,
        )

    @staticmethod
    def _build_explanation(
        final_decision: str,
        rules_evaluated: list[RuleTrace],
        rules_matched: list[RuleTrace],
    ) -> str:
        if not rules_matched:
            return f"No rules matched. Evaluated {len(rules_evaluated)} active rule(s)."

        winner = rules_matched[0]
        explanation = (
            f"Final decision: {final_decision} "
            f"(highest-priority match: '{winner.rule_name}', priority {winner.priority})."
        )
        if len(rules_matched) > 1:
            additional = ", ".join(
                f"{trace.decision_outcome} ('{trace.rule_name}')"
                for trace in rules_matched[1:]
            )
            explanation += f" Additional matches: {additional}."
        return explanation
