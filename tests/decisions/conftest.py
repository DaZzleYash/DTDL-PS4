"""Shared fixtures for decisions module tests."""

from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.decisions.service import DecisionEngineService
from app.main import app
from app.rules.models import Rule
from app.schemas.decision import EvaluateRequest


def make_rule(
    *,
    rule_id: int,
    name: str,
    priority: int,
    decision_outcome: str,
    condition: dict | None = None,
    condition_json: str | None = None,
    active: bool = True,
    category: str | None = None,
) -> Rule:
    return Rule(
        id=rule_id,
        name=name,
        priority=priority,
        active=active,
        category=category,
        condition_json=condition_json if condition_json is not None else json.dumps(condition),
        decision_outcome=decision_outcome,
        version=1,
    )


class FakeRuleRepository:
    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def list_active_ordered_by_priority(self, category: str | None = None) -> list[Rule]:
        rules = [rule for rule in self._rules if rule.active]
        if category is not None:
            rules = [rule for rule in rules if rule.category == category]
        return sorted(rules, key=lambda rule: (rule.priority, rule.id))


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def decision_service() -> DecisionEngineService:
    return DecisionEngineService(FakeRuleRepository([]))


SAMPLE_CONTEXT = {
    "applicant": {"creditScore": 720, "employmentStatus": "EMPLOYED"},
    "loan": {"amount": 25000, "termMonths": 36},
    "risk_flags": {"hasDefaulted": False, "debtToIncomeRatio": 0.3},
}

SAMPLE_REQUEST = EvaluateRequest(context=SAMPLE_CONTEXT)
