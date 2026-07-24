"""Rule business logic — owned by Contributor B."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.engine.registry import ConditionEvaluatorRegistry
from app.exceptions import InvalidRuleError, RuleNotFoundError
from app.rules.models import Rule
from app.rules.repository import RuleRepository
from app.schemas.rule import RuleCreate, RuleOut, RuleUpdate


class RuleService:
    def __init__(
        self,
        db: Session,
        registry: ConditionEvaluatorRegistry | None = None,
    ) -> None:
        self._repo = RuleRepository(db)
        self._registry = registry or ConditionEvaluatorRegistry()

    def create(self, payload: RuleCreate) -> RuleOut:
        self._registry.validate(payload.condition)
        rule = Rule(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            priority=payload.priority,
            active=payload.active,
            condition_json=json.dumps(payload.condition),
            decision_outcome=payload.decision_outcome,
            decision_metadata_json=self._serialize_metadata(payload.decision_metadata),
            version=1,
        )
        return self._to_out(self._repo.create(rule))

    def update(self, rule_id: int, payload: RuleUpdate) -> RuleOut:
        rule = self._get_or_raise(rule_id)
        self._registry.validate(payload.condition)
        rule.name = payload.name
        rule.description = payload.description
        rule.category = payload.category
        rule.priority = payload.priority
        rule.active = payload.active
        rule.condition_json = json.dumps(payload.condition)
        rule.decision_outcome = payload.decision_outcome
        rule.decision_metadata_json = self._serialize_metadata(payload.decision_metadata)
        rule.version += 1
        rule.updated_at = datetime.now(timezone.utc)
        return self._to_out(self._repo.update(rule))

    def set_active(self, rule_id: int, active: bool) -> RuleOut:
        rule = self._get_or_raise(rule_id)
        rule.active = active
        rule.version += 1
        rule.updated_at = datetime.now(timezone.utc)
        return self._to_out(self._repo.update(rule))

    def delete(self, rule_id: int) -> None:
        if not self._repo.delete(rule_id):
            raise RuleNotFoundError(rule_id)

    def get(self, rule_id: int) -> RuleOut:
        return self._to_out(self._get_or_raise(rule_id))

    def list(self, category: str | None = None) -> list[RuleOut]:
        return [self._to_out(rule) for rule in self._repo.list(category=category)]

    def _get_or_raise(self, rule_id: int) -> Rule:
        rule = self._repo.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(rule_id)
        return rule

    @staticmethod
    def _serialize_metadata(metadata: dict | None) -> str | None:
        if metadata is None:
            return None
        return json.dumps(metadata)

    def _to_out(self, rule: Rule) -> RuleOut:
        try:
            condition = json.loads(rule.condition_json)
        except json.JSONDecodeError as exc:
            raise InvalidRuleError(f"Stored condition for rule {rule.id} is invalid JSON") from exc

        decision_metadata = None
        if rule.decision_metadata_json is not None:
            try:
                decision_metadata = json.loads(rule.decision_metadata_json)
            except json.JSONDecodeError as exc:
                raise InvalidRuleError(
                    f"Stored decision metadata for rule {rule.id} is invalid JSON"
                ) from exc

        return RuleOut(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            category=rule.category,
            priority=rule.priority,
            active=rule.active,
            condition=condition,
            decision_outcome=rule.decision_outcome,
            decision_metadata=decision_metadata,
            version=rule.version,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
