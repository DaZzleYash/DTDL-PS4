"""Shared fixtures for rules module tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.rules.models import Rule  # noqa: F401 — register model with metadata


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


VALID_RULE_PAYLOAD = {
    "name": "Minimum Credit Score",
    "description": "Requires credit score of at least 650",
    "category": "ELIGIBILITY",
    "priority": 10,
    "active": True,
    "condition": {
        "type": "NUMERIC",
        "field": "applicant.creditScore",
        "operator": "GTE",
        "value": 650,
    },
    "decision_outcome": "APPROVE",
    "decision_metadata": {"riskTier": "A"},
}
