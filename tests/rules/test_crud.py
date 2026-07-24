"""Rule CRUD and validation tests — Contributor B."""

from tests.rules.conftest import VALID_RULE_PAYLOAD


def test_create_rule_returns_201(client) -> None:
    response = client.post("/api/rules/", json=VALID_RULE_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == VALID_RULE_PAYLOAD["name"]
    assert body["version"] == 1
    assert body["condition"]["type"] == "NUMERIC"


def test_get_rule_returns_200(client) -> None:
    created = client.post("/api/rules/", json=VALID_RULE_PAYLOAD).json()
    response = client.get(f"/api/rules/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == VALID_RULE_PAYLOAD["name"]


def test_list_rules_returns_all(client) -> None:
    client.post("/api/rules/", json=VALID_RULE_PAYLOAD)
    risk_payload = {
        **VALID_RULE_PAYLOAD,
        "name": "High DTI",
        "category": "RISK",
        "priority": 20,
        "decision_outcome": "MANUAL_REVIEW",
    }
    client.post("/api/rules/", json=risk_payload)

    response = client.get("/api/rules/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_rules_filters_by_category(client) -> None:
    client.post("/api/rules/", json=VALID_RULE_PAYLOAD)
    risk_payload = {
        **VALID_RULE_PAYLOAD,
        "name": "High DTI",
        "category": "RISK",
    }
    client.post("/api/rules/", json=risk_payload)

    response = client.get("/api/rules/", params={"category": "RISK"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["category"] == "RISK"


def test_update_rule_increments_version(client) -> None:
    created = client.post("/api/rules/", json=VALID_RULE_PAYLOAD).json()
    updated_payload = {
        **VALID_RULE_PAYLOAD,
        "priority": 15,
        "description": "Updated description",
    }
    response = client.put(f"/api/rules/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["priority"] == 15
    assert body["version"] == 2


def test_patch_active_toggles_rule(client) -> None:
    created = client.post("/api/rules/", json=VALID_RULE_PAYLOAD).json()
    response = client.patch(
        f"/api/rules/{created['id']}/active",
        json={"active": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is False
    assert body["version"] == 2


def test_delete_rule_returns_204(client) -> None:
    created = client.post("/api/rules/", json=VALID_RULE_PAYLOAD).json()
    response = client.delete(f"/api/rules/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/rules/{created['id']}").status_code == 404


def test_create_rule_with_invalid_condition_returns_400(client) -> None:
    payload = {
        **VALID_RULE_PAYLOAD,
        "condition": {"type": "UNKNOWN", "field": "x", "operator": "EQUALS", "value": 1},
    }
    response = client.post("/api/rules/", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert "Unknown condition type" in body["message"]


def test_get_missing_rule_returns_404(client) -> None:
    response = client.get("/api/rules/999")
    assert response.status_code == 404
    body = response.json()
    assert "999" in body["message"]


def test_delete_missing_rule_returns_404(client) -> None:
    response = client.delete("/api/rules/999")
    assert response.status_code == 404
