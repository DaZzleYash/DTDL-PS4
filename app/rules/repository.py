"""Rule persistence layer — owned by Contributor B."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.rules.models import Rule


class RuleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, rule_id: int) -> Rule | None:
        return self._db.get(Rule, rule_id)

    def list(self, category: str | None = None) -> list[Rule]:
        stmt = select(Rule).order_by(Rule.priority.asc(), Rule.id.asc())
        if category is not None:
            stmt = stmt.where(Rule.category == category)
        return list(self._db.scalars(stmt).all())

    def list_active_ordered_by_priority(self, category: str | None = None) -> list[Rule]:
        stmt = (
            select(Rule)
            .where(Rule.active.is_(True))
            .order_by(Rule.priority.asc(), Rule.id.asc())
        )
        if category is not None:
            stmt = stmt.where(Rule.category == category)
        return list(self._db.scalars(stmt).all())

    def create(self, rule: Rule) -> Rule:
        self._db.add(rule)
        self._db.commit()
        self._db.refresh(rule)
        return rule

    def update(self, rule: Rule) -> Rule:
        self._db.commit()
        self._db.refresh(rule)
        return rule

    def delete(self, rule_id: int) -> bool:
        rule = self.get(rule_id)
        if rule is None:
            return False
        self._db.delete(rule)
        self._db.commit()
        return True
