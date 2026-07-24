"""Live API smoke test — seeds DB and exercises every endpoint."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://localhost:8000"


@dataclass
class Result:
    name: str
    method: str
    path: str
    status: int
    ok: bool
    detail: str = ""


results: list[Result] = []


def record(name: str, method: str, path: str, response: httpx.Response, ok: bool, detail: str = "") -> None:
    results.append(
        Result(name, method, path, response.status_code, ok, detail or response.text[:200])
    )
    icon = "PASS" if ok else "FAIL"
    print(f"[{icon}] {method} {path} -> {response.status_code} | {name}")
    if not ok:
        print(f"       {detail or response.text[:300]}")


def setup_database() -> None:
    print("\n=== Database setup ===")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=ROOT)
    seed = subprocess.run([sys.executable, "-m", "app.finance.seed_rules"], cwd=ROOT)
    if seed.returncode != 0:
        raise SystemExit("seed_rules failed")
    print("Migrations applied and finance rules seeded.\n")


def main() -> int:
    setup_database()

    print("=== Endpoint tests ===")
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        # Health
        r = client.get("/health")
        record("Health check", "GET", "/health", r, r.status_code == 200 and r.json().get("status") == "healthy")

        # List all rules
        r = client.get("/api/rules/")
        rules = r.json()
        record(
            "List rules",
            "GET",
            "/api/rules/",
            r,
            r.status_code == 200 and len(rules) >= 5,
            f"{len(rules)} rule(s) in DB",
        )

        # List by category
        r = client.get("/api/rules/", params={"category": "RISK"})
        record(
            "List rules by category",
            "GET",
            "/api/rules/?category=RISK",
            r,
            r.status_code == 200 and all(rule["category"] == "RISK" for rule in r.json()),
        )

        first_id = rules[0]["id"]
        r = client.get(f"/api/rules/{first_id}")
        record("Get rule by ID", "GET", f"/api/rules/{first_id}", r, r.status_code == 200)

        # Create rule
        new_rule = {
            "name": "API Test Rule",
            "description": "Created by endpoint smoke test",
            "category": "TEST",
            "priority": 99,
            "active": True,
            "condition": {
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 500,
            },
            "decision_outcome": "APPROVE",
        }
        r = client.post("/api/rules/", json=new_rule)
        created = r.json()
        created_id = created.get("id")
        record("Create rule", "POST", "/api/rules/", r, r.status_code == 201 and created_id is not None)

        # Update rule
        updated_payload = {**new_rule, "name": "API Test Rule Updated", "priority": 100}
        r = client.put(f"/api/rules/{created_id}", json=updated_payload)
        record(
            "Update rule",
            "PUT",
            f"/api/rules/{created_id}",
            r,
            r.status_code == 200 and r.json()["name"] == "API Test Rule Updated",
        )

        # Deactivate rule
        r = client.patch(f"/api/rules/{created_id}/active", json={"active": False})
        record(
            "Deactivate rule",
            "PATCH",
            f"/api/rules/{created_id}/active",
            r,
            r.status_code == 200 and r.json()["active"] is False,
        )

        # Reactivate rule
        r = client.patch(f"/api/rules/{created_id}/active", json={"active": True})
        record(
            "Reactivate rule",
            "PATCH",
            f"/api/rules/{created_id}/active",
            r,
            r.status_code == 200 and r.json()["active"] is True,
        )

        # Invalid rule -> 400
        r = client.post("/api/rules/", json={**new_rule, "condition": {"type": "UNKNOWN"}})
        record("Invalid rule rejected", "POST", "/api/rules/", r, r.status_code == 400)

        # Missing rule -> 404
        r = client.get("/api/rules/999999")
        record("Missing rule 404", "GET", "/api/rules/999999", r, r.status_code == 404)

        # Decisions — sample scenarios
        from app.finance.sample_requests import EXPECTED_DECISIONS, SAMPLE_REQUESTS

        for scenario, payload in SAMPLE_REQUESTS.items():
            r = client.post("/api/decisions/evaluate", json=payload)
            body = r.json()
            expected = EXPECTED_DECISIONS[scenario]
            ok = r.status_code == 200 and body.get("final_decision") == expected
            record(
                f"Evaluate: {scenario}",
                "POST",
                "/api/decisions/evaluate",
                r,
                ok,
                f"expected={expected}, got={body.get('final_decision')}",
            )

        # Bulk evaluate
        bulk_payload = list(SAMPLE_REQUESTS.values())
        r = client.post("/api/decisions/evaluate/bulk", json=bulk_payload)
        bulk = r.json()
        record(
            "Bulk evaluate",
            "POST",
            "/api/decisions/evaluate/bulk",
            r,
            r.status_code == 200 and len(bulk) == len(SAMPLE_REQUESTS),
            f"{len(bulk)} responses",
        )

        # Delete test rule
        r = client.delete(f"/api/rules/{created_id}")
        record("Delete rule", "DELETE", f"/api/rules/{created_id}", r, r.status_code == 204)

        r = client.get(f"/api/rules/{created_id}")
        record("Deleted rule 404", "GET", f"/api/rules/{created_id}", r, r.status_code == 404)

    passed = sum(1 for x in results if x.ok)
    failed = len(results) - passed
    print(f"\n=== Summary: {passed}/{len(results)} passed, {failed} failed ===")
    if failed:
        print("\nFailed checks:")
        for x in results:
            if not x.ok:
                print(f"  - {x.name}: {x.method} {x.path} ({x.status}) {x.detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
