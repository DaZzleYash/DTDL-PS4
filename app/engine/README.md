"""
Rules Engine Core — owned by Contributor A.

Pure Python condition evaluator. No database, no FastAPI, no finance knowledge.

Deliverables:
  - app/engine/context.py       EvaluationContext
  - app/engine/result.py        EvaluationResult
  - app/engine/base.py          ConditionEvaluator protocol
  - app/engine/registry.py      ConditionEvaluatorRegistry
  - app/engine/evaluators/      numeric, string, boolean, date

Branch: feat/engine-core
Tests:  tests/engine/
"""
