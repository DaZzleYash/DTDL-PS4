"""Shared decision schemas — owner: Contributor C (agreed in Phase 0)."""

from datetime import datetime

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    context: dict  # the loan application payload
    category: str | None = None  # optional: only evaluate rules in this category


class RuleTrace(BaseModel):
    rule_id: int
    rule_name: str
    priority: int
    matched: bool
    decision_outcome: str | None
    explanation: str


class DecisionResponse(BaseModel):
    final_decision: str  # winning outcome, or "NO_DECISION"
    matched_decisions: list[str]
    explanation: str
    rules_evaluated: list[RuleTrace]
    rules_matched: list[RuleTrace]
    rules_rejected: list[RuleTrace]
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
