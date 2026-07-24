"""End-to-end integration tests — Contributor E (Phase 2).

Seeds finance rules, exercises the full HTTP stack, and asserts explainable
decisions match the demo scenarios defined in app/finance/sample_requests.py.
"""

import pytest
from fastapi.testclient import TestClient

from app.finance.sample_requests import (
    EXPECTED_DECISIONS,
    EXPECTED_MATCHED_RULE_NAMES,
    SAMPLE_REQUESTS,
)

VALID_RULE_PAYLOAD = {
    "name": "Integration Test Rule",
    "description": "Temporary rule for integration testing",
    "category": "TEST",
    "priority": 99,
    "active": True,
    "condition": {
        "type": "NUMERIC",
        "field": "applicant.creditScore",
        "operator": "GTE",
        "value": 650,
    },
    "decision_outcome": "APPROVE",
}


def test_health_endpoint(seeded_client: TestClient) -> None:
    response = seeded_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_openapi_lists_rules_and_decisions(seeded_client: TestClient) -> None:
    response = seeded_client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/rules/" in paths
    assert "/api/decisions/evaluate" in paths
    assert "/api/decisions/evaluate/bulk" in paths


def test_seeded_rules_are_listed(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/rules/")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) == 5
    names = {rule["name"] for rule in rules}
    assert "Minimum Credit Score" in names
    assert "Prior Default Block" in names


@pytest.mark.parametrize("scenario", list(SAMPLE_REQUESTS))
def test_evaluate_sample_loan_payload(
    seeded_client: TestClient,
    scenario: str,
) -> None:
    payload = SAMPLE_REQUESTS[scenario]
    response = seeded_client.post("/api/decisions/evaluate", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["final_decision"] == EXPECTED_DECISIONS[scenario]
    matched_names = {trace["rule_name"] for trace in body["rules_matched"]}
    assert EXPECTED_MATCHED_RULE_NAMES[scenario] <= matched_names
    assert len(body["rules_evaluated"]) == 5
    assert body["explanation"]
    assert body["evaluated_at"]


def test_evaluate_bulk(seeded_client: TestClient) -> None:
    payloads = list(SAMPLE_REQUESTS.values())[:2]
    response = seeded_client.post("/api/decisions/evaluate/bulk", json=payloads)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert all(result["final_decision"] for result in results)


def test_no_match_returns_no_decision(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/decisions/evaluate",
        json={
            "context": {
                "applicant": {"creditScore": 400},
                "loan": {"amount": 1000},
                "risk_flags": {"hasDefaulted": False, "debtToIncomeRatio": 0.1},
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["final_decision"] == "NO_DECISION"
    assert body["rules_matched"] == []
    assert len(body["rules_rejected"]) == 5


def test_unknown_condition_type_returns_400(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/rules/",
        json={
            **VALID_RULE_PAYLOAD,
            "condition": {"type": "UNKNOWN", "field": "x", "operator": "EQUALS", "value": 1},
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == 400
    assert "Supported types" in body["message"]


def test_missing_rule_returns_404(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/rules/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["status"] == 404
    assert "99999" in body["message"]
