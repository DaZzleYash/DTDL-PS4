"""Health endpoint and platform tests — Contributor E."""

from fastapi.testclient import TestClient


def test_health_returns_healthy(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "timestamp" in data


def test_openapi_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
