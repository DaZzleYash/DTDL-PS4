"""Shared fixtures for finance module tests."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.decisions.service import DecisionEngineService
from app.finance.seed_rules import seed_rules
from app.rules.models import Rule  # noqa: F401 — register model with metadata
from app.rules.repository import RuleRepository


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
def seeded_decision_service(db_session: Session) -> DecisionEngineService:
    created = seed_rules(db_session)
    assert len(created) == 7
    return DecisionEngineService(RuleRepository(db_session))
