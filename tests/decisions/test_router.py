"""Decision API tests — Contributor C."""

import json

from app.rules.models import Rule
from tests.decisions.conftest import SAMPLE_CONTEXT


def _create_rule(db_session, **overrides) -> Rule:
    payload = {
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
        "decision_metadata": None,
        **overrides,
    }
    rule = Rule(
        name=payload["name"],
        description=payload.get("description"),
        category=payload.get("category"),
        priority=payload["priority"],
        active=payload["active"],
        condition_json=json.dumps(payload["condition"]),
        decision_outcome=payload["decision_outcome"],
        decision_metadata_json=None,
        version=1,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


def test_evaluate_endpoint_returns_decision(client, db_session) -> None:
    _create_rule(db_session)

    response = client.post(
        "/api/decisions/evaluate",
        json={"context": SAMPLE_CONTEXT},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["final_decision"] == "APPROVE"
    assert body["matched_decisions"] == ["APPROVE"]
    assert len(body["rules_matched"]) == 1


def test_evaluate_bulk_endpoint_returns_list(client, db_session) -> None:
    _create_rule(db_session)

    response = client.post(
        "/api/decisions/evaluate/bulk",
        json=[
            {"context": SAMPLE_CONTEXT},
            {"context": {"applicant": {"creditScore": 500}}},
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["final_decision"] == "APPROVE"
    assert body[1]["final_decision"] == "NO_DECISION"
