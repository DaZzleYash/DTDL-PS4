"""Evaluation result types — owned by Contributor A."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of evaluating a single condition node."""

    matched: bool
    explanation: str
