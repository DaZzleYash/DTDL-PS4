#!/usr/bin/env python3
"""
Finance Decision Engine — Jury Test Report Generator

Runs the full automated test suite AND structured demo scenarios,
then writes a detailed HTML + Markdown report for hackathon presentation.

Usage (from repo root, with venv activated):
    python scripts/run_jury_test_report.py

Optional:
    python scripts/run_jury_test_report.py --open   # open HTML report in browser (Windows)
"""

from __future__ import annotations

import argparse
import html
import subprocess
import sys
import webbrowser
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def configure_console() -> None:
    """Use UTF-8 on stdout/stderr when supported (avoids Windows cp1252 crashes)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def console_print(message: str = "") -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    text = message + "\n"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.write(text.encode(encoding, errors="replace").decode(encoding))
    sys.stdout.flush()

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CaseResult:
    section: str
    name: str
    description: str
    passed: bool
    expected: str = ""
    actual: str = ""
    detail: str = ""
    duration_ms: float = 0.0


@dataclass
class PytestCase:
    classname: str
    name: str
    status: str  # passed | failed | skipped | error
    message: str = ""
    duration_sec: float = 0.0


@dataclass
class Report:
    generated_at: str
    pytest_cases: list[PytestCase] = field(default_factory=list)
    demo_cases: list[CaseResult] = field(default_factory=list)
    pytest_stdout: str = ""
    pytest_exit_code: int = 0
    pytest_duration_sec: float = 0.0

    @property
    def pytest_passed(self) -> int:
        return sum(1 for c in self.pytest_cases if c.status == "passed")

    @property
    def pytest_failed(self) -> int:
        return sum(1 for c in self.pytest_cases if c.status == "failed")

    @property
    def pytest_skipped(self) -> int:
        return sum(1 for c in self.pytest_cases if c.status == "skipped")

    @property
    def pytest_errors(self) -> int:
        return sum(1 for c in self.pytest_cases if c.status == "error")

    @property
    def demo_passed(self) -> int:
        return sum(1 for c in self.demo_cases if c.passed)

    @property
    def demo_failed(self) -> int:
        return sum(1 for c in self.demo_cases if not c.passed)

    @property
    def all_passed(self) -> bool:
        return self.pytest_exit_code == 0 and self.demo_failed == 0


# ---------------------------------------------------------------------------
# Pytest runner
# ---------------------------------------------------------------------------


def run_pytest_suite() -> tuple[list[PytestCase], str, int, float]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    junit_path = REPORTS_DIR / "junit.xml"

    started = perf_counter()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--tb=line",
            f"--junitxml={junit_path}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    duration = perf_counter() - started

    cases: list[PytestCase] = []
    if junit_path.exists():
        tree = ET.parse(junit_path)
        root = tree.getroot()
        for suite in root.iter("testsuite"):
            for case in suite.iter("testcase"):
                status = "passed"
                message = ""
                for child in case:
                    if child.tag in {"failure", "error"}:
                        status = "failed" if child.tag == "failure" else "error"
                        message = (child.text or child.get("message", "")).strip()
                    elif child.tag == "skipped":
                        status = "skipped"
                        message = (child.text or child.get("message", "")).strip()
                cases.append(
                    PytestCase(
                        classname=case.get("classname", ""),
                        name=case.get("name", ""),
                        status=status,
                        message=message[:500],
                        duration_sec=float(case.get("time", 0) or 0),
                    )
                )

    return cases, proc.stdout + proc.stderr, proc.returncode, duration


# ---------------------------------------------------------------------------
# Jury demo scenarios (live HTTP stack via TestClient)
# ---------------------------------------------------------------------------


def run_jury_demo_cases() -> list[CaseResult]:
    from collections.abc import Generator

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.core.database import Base, get_db
    from app.finance.sample_requests import (
        EXPECTED_DECISIONS,
        EXPECTED_MATCHED_RULE_NAMES,
        SAMPLE_REQUESTS,
    )
    from app.finance.seed_rules import seed_rules
    from app.main import app
    from app.rules.models import Rule  # noqa: F401

    results: list[CaseResult] = []

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = session_factory()
    seed_rules(db)

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    def record(
        section: str,
        name: str,
        description: str,
        passed: bool,
        expected: str = "",
        actual: str = "",
        detail: str = "",
        duration_ms: float = 0.0,
    ) -> None:
        results.append(
            CaseResult(section, name, description, passed, expected, actual, detail, duration_ms)
        )
        icon = "PASS" if passed else "FAIL"
        console_print(f"  [{icon}] {name}")

    with TestClient(app) as client:
        # --- Platform ---
        t0 = perf_counter()
        r = client.get("/health")
        body = r.json()
        record(
            "Platform",
            "Health check",
            "API is running and returns healthy status",
            r.status_code == 200 and body.get("status") == "healthy",
            expected="status=healthy, HTTP 200",
            actual=f"status={body.get('status')}, HTTP {r.status_code}",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.get("/openapi.json")
        paths = r.json().get("paths", {}) if r.status_code == 200 else {}
        record(
            "Platform",
            "OpenAPI documents Rules & Decisions",
            "Swagger spec lists all public API groups",
            "/api/rules/" in paths and "/api/decisions/evaluate" in paths,
            expected="Rules + Decisions paths present",
            actual=f"rules={'/api/rules/' in paths}, decisions={'/api/decisions/evaluate' in paths}",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        # --- Module B: Rules ---
        t0 = perf_counter()
        r = client.get("/api/rules/")
        rules = r.json() if r.status_code == 200 else []
        record(
            "Rules (B)",
            "List seeded finance rules",
            "Seven demo rules loaded for jury scenarios",
            r.status_code == 200 and len(rules) == 7,
            expected="7 rules",
            actual=f"{len(rules)} rules",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.post(
            "/api/rules/",
            json={
                "name": "Jury Test Rule",
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
            },
        )
        created = r.json() if r.status_code == 201 else {}
        record(
            "Rules (B)",
            "Create rule via API",
            "New rule persisted with valid condition",
            r.status_code == 201 and created.get("name") == "Jury Test Rule",
            expected="HTTP 201, name=Jury Test Rule",
            actual=f"HTTP {r.status_code}, name={created.get('name')}",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.post(
            "/api/rules/",
            json={
                "name": "Bad Rule",
                "priority": 1,
                "active": True,
                "condition": {"type": "UNKNOWN"},
                "decision_outcome": "REJECT",
            },
        )
        record(
            "Rules (B)",
            "Reject invalid rule",
            "Unknown condition type returns HTTP 400",
            r.status_code == 400,
            expected="HTTP 400",
            actual=f"HTTP {r.status_code}",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.get("/api/rules/99999")
        record(
            "Rules (B)",
            "Missing rule returns 404",
            "Structured error for unknown rule id",
            r.status_code == 404,
            expected="HTTP 404",
            actual=f"HTTP {r.status_code}",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        # --- Module C: Decisions (your module) ---
        for scenario, payload in SAMPLE_REQUESTS.items():
            t0 = perf_counter()
            r = client.post("/api/decisions/evaluate", json=payload)
            body = r.json() if r.status_code == 200 else {}
            expected = EXPECTED_DECISIONS[scenario]
            actual = body.get("final_decision", "ERROR")
            matched = {t["rule_name"] for t in body.get("rules_matched", [])}
            rules_ok = EXPECTED_MATCHED_RULE_NAMES[scenario] <= matched
            record(
                "Decisions (C)",
                f"Demo: {scenario}",
                f"Loan scenario → expected {expected}",
                r.status_code == 200 and actual == expected and rules_ok,
                expected=f"{expected}, rules={sorted(EXPECTED_MATCHED_RULE_NAMES[scenario])}",
                actual=f"{actual}, rules={sorted(matched)}",
                detail=body.get("explanation", "")[:200],
                duration_ms=(perf_counter() - t0) * 1000,
            )

        t0 = perf_counter()
        r = client.post(
            "/api/decisions/evaluate",
            json={
                "context": {
                    "applicant": {"creditScore": 400},
                    "loan": {"amount": 1000},
                    "risk_flags": {"hasDefaulted": False, "debtToIncomeRatio": 0.1},
                }
            },
        )
        body = r.json() if r.status_code == 200 else {}
        record(
            "Decisions (C)",
            "No matching rules -> NO_DECISION",
            "Applicant matches nothing; full trace still returned",
            body.get("final_decision") == "NO_DECISION" and body.get("rules_matched") == [],
            expected="NO_DECISION, 0 matches",
            actual=f"{body.get('final_decision')}, {len(body.get('rules_matched', []))} matches",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.post(
            "/api/decisions/evaluate/bulk",
            json=list(SAMPLE_REQUESTS.values())[:3],
        )
        bulk = r.json() if r.status_code == 200 else []
        record(
            "Decisions (C)",
            "Bulk evaluate (3 applications)",
            "Batch endpoint returns one decision per request",
            r.status_code == 200 and len(bulk) == 3,
            expected="HTTP 200, 3 results",
            actual=f"HTTP {r.status_code}, {len(bulk)} results",
            duration_ms=(perf_counter() - t0) * 1000,
        )

        t0 = perf_counter()
        r = client.post(
            "/api/decisions/evaluate",
            json={
                "context": {
                    "applicant": {"creditScore": 720},
                    "risk_flags": {"debtToIncomeRatio": 0.55},
                }
            },
        )
        body = r.json() if r.status_code == 200 else {}
        winner = body.get("rules_matched", [{}])[0] if body.get("rules_matched") else {}
        record(
            "Decisions (C)",
            "Priority: lowest number wins",
            "When multiple rules match, priority 10 beats priority 20",
            body.get("final_decision") == "APPROVE"
            and winner.get("rule_name") == "Minimum Credit Score",
            expected="APPROVE from Minimum Credit Score (priority 10)",
            actual=f"{body.get('final_decision')} from {winner.get('rule_name')} (priority {winner.get('priority')})",
            detail=body.get("explanation", "")[:200],
            duration_ms=(perf_counter() - t0) * 1000,
        )

    app.dependency_overrides.clear()
    db.close()
    Base.metadata.drop_all(bind=engine)
    return results


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def _module_from_classname(classname: str) -> str:
    if "tests.engine" in classname:
        return "Engine (A)"
    if "tests.rules" in classname:
        return "Rules (B)"
    if "tests.decisions" in classname:
        return "Decisions (C)"
    if "tests.finance" in classname:
        return "Finance (D)"
    if "tests.integration" in classname:
        return "Integration (E)"
    return "Other"


def write_markdown(report: Report, path: Path) -> None:
    lines = [
        "# Finance Decision Engine — Jury Test Report",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Overall verdict:** {'✅ ALL PASSED' if report.all_passed else '❌ FAILURES DETECTED'}",
        "",
        "## Summary",
        "",
        "| Suite | Passed | Failed | Skipped | Total |",
        "|-------|--------|--------|---------|-------|",
        f"| Automated pytest | {report.pytest_passed} | {report.pytest_failed + report.pytest_errors} | {report.pytest_skipped} | {len(report.pytest_cases)} |",
        f"| Jury demo scenarios | {report.demo_passed} | {report.demo_failed} | 0 | {len(report.demo_cases)} |",
        "",
        f"Pytest duration: {report.pytest_duration_sec:.1f}s",
        "",
        "## Jury Demo Scenarios",
        "",
        "| Section | Test | Expected | Actual | Result |",
        "|---------|------|----------|--------|--------|",
    ]
    for case in report.demo_cases:
        status = "PASS" if case.passed else "FAIL"
        lines.append(
            f"| {case.section} | {case.name} | {case.expected} | {case.actual} | {status} |"
        )

    lines.extend(["", "## Automated Tests by Module", ""])
    by_module: dict[str, list[PytestCase]] = {}
    for case in report.pytest_cases:
        mod = _module_from_classname(case.classname)
        by_module.setdefault(mod, []).append(case)

    for mod in sorted(by_module.keys()):
        cases = by_module[mod]
        passed = sum(1 for c in cases if c.status == "passed")
        lines.append(f"### {mod} — {passed}/{len(cases)} passed")
        lines.append("")
        for c in cases:
            icon = "✅" if c.status == "passed" else "❌"
            lines.append(f"- {icon} `{c.name}` ({c.duration_sec:.2f}s)")
            if c.message:
                lines.append(f"  - {c.message[:200]}")
        lines.append("")

    if report.pytest_failed or report.pytest_errors:
        lines.extend(["## Failures", ""])
        for c in report.pytest_cases:
            if c.status in {"failed", "error"}:
                lines.append(f"- **{c.classname}::{c.name}**")
                lines.append(f"  ```")
                lines.append(f"  {c.message}")
                lines.append(f"  ```")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(report: Report, path: Path) -> None:
    demo_rows = ""
    for case in report.demo_cases:
        cls = "pass" if case.passed else "fail"
        demo_rows += f"""
        <tr class="{cls}">
          <td>{html.escape(case.section)}</td>
          <td><strong>{html.escape(case.name)}</strong><br><small>{html.escape(case.description)}</small></td>
          <td><code>{html.escape(case.expected)}</code></td>
          <td><code>{html.escape(case.actual)}</code></td>
          <td>{'PASS' if case.passed else 'FAIL'}</td>
          <td>{case.duration_ms:.0f} ms</td>
        </tr>"""

    by_module: dict[str, list[PytestCase]] = {}
    for case in report.pytest_cases:
        mod = _module_from_classname(case.classname)
        by_module.setdefault(mod, []).append(case)

    module_sections = ""
    for mod in sorted(by_module.keys()):
        cases = by_module[mod]
        passed = sum(1 for c in cases if c.status == "passed")
        rows = ""
        for c in cases:
            cls = "pass" if c.status == "passed" else "fail"
            rows += f"""<tr class="{cls}"><td>{html.escape(c.name)}</td><td>{c.status.upper()}</td><td>{c.duration_sec:.2f}s</td></tr>"""
        module_sections += f"""
        <h3>{html.escape(mod)} <span class="badge">{passed}/{len(cases)} passed</span></h3>
        <table><thead><tr><th>Test</th><th>Status</th><th>Time</th></tr></thead><tbody>{rows}</tbody></table>"""

    verdict = "ALL TESTS PASSED" if report.all_passed else "SOME TESTS FAILED"
    verdict_class = "verdict-pass" if report.all_passed else "verdict-fail"

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Finance Decision Engine — Jury Test Report</title>
  <style>
    :root {{ font-family: Inter, Segoe UI, sans-serif; color: #0f172a; }}
    body {{ max-width: 1100px; margin: 0 auto; padding: 32px; background: #f8fafc; }}
    h1 {{ margin-bottom: 4px; }}
    .subtitle {{ color: #64748b; margin-bottom: 24px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
    .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    .card h2 {{ margin: 0 0 8px; font-size: 14px; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }}
    .card .num {{ font-size: 32px; font-weight: 700; }}
    .verdict-pass {{ background: #ecfdf5; color: #065f46; padding: 16px 20px; border-radius: 12px; font-weight: 700; margin-bottom: 24px; }}
    .verdict-fail {{ background: #fef2f2; color: #991b1b; padding: 16px 20px; border-radius: 12px; font-weight: 700; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
    th {{ background: #f1f5f9; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    tr.pass td:last-child {{ color: #059669; font-weight: 700; }}
    tr.fail {{ background: #fff1f2; }}
    tr.fail td:last-child {{ color: #dc2626; font-weight: 700; }}
    .badge {{ background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 999px; font-size: 12px; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
    h3 {{ margin-top: 32px; }}
    footer {{ margin-top: 40px; color: #94a3b8; font-size: 13px; }}
  </style>
</head>
<body>
  <h1>Finance Decision Engine</h1>
  <p class="subtitle">Deutsche Telekom Digital Labs · PS4 Hackathon · Test Report · {html.escape(report.generated_at)}</p>

  <div class="{verdict_class}">{verdict}</div>

  <div class="cards">
    <div class="card"><h2>Pytest passed</h2><div class="num">{report.pytest_passed}</div></div>
    <div class="card"><h2>Pytest failed</h2><div class="num">{report.pytest_failed + report.pytest_errors}</div></div>
    <div class="card"><h2>Demo scenarios passed</h2><div class="num">{report.demo_passed}</div></div>
    <div class="card"><h2>Demo scenarios failed</h2><div class="num">{report.demo_failed}</div></div>
    <div class="card"><h2>Total automated tests</h2><div class="num">{len(report.pytest_cases)}</div></div>
  </div>

  <h2>Jury Demo Scenarios</h2>
  <p>End-to-end checks across Platform, Rules (B), and Decisions (C) using seeded finance rules.</p>
  <table>
    <thead>
      <tr><th>Module</th><th>Scenario</th><th>Expected</th><th>Actual</th><th>Result</th><th>Time</th></tr>
    </thead>
    <tbody>{demo_rows}</tbody>
  </table>

  <h2>Automated Test Suite (pytest)</h2>
  <p>Full unit and integration coverage: Engine (A), Rules (B), Decisions (C), Finance (D), Integration (E).</p>
  {module_sections}

  <footer>
    Generated by scripts/run_jury_test_report.py · Project: DTDL-PS4 · Run: pytest + live API demo via TestClient
  </footer>
</body>
</html>"""
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description="Run all tests and generate jury report")
    parser.add_argument("--open", action="store_true", help="Open HTML report in browser after generation")
    args = parser.parse_args()

    console_print("=" * 60)
    console_print("  Finance Decision Engine - Jury Test Report")
    console_print("=" * 60)

    report = Report(generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))

    console_print("\n[1/2] Running full pytest suite (tests/)...")
    cases, stdout, exit_code, duration = run_pytest_suite()
    report.pytest_cases = cases
    report.pytest_stdout = stdout
    report.pytest_exit_code = exit_code
    report.pytest_duration_sec = duration
    console_print(f"      Pytest: {report.pytest_passed} passed, "
                    f"{report.pytest_failed + report.pytest_errors} failed, "
                    f"{report.pytest_skipped} skipped ({duration:.1f}s)")

    console_print("\n[2/2] Running jury demo scenarios (HTTP stack)...")
    report.demo_cases = run_jury_demo_cases()
    console_print(f"      Demo:   {report.demo_passed} passed, {report.demo_failed} failed")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = REPORTS_DIR / "jury_test_report.html"
    md_path = REPORTS_DIR / "jury_test_report.md"
    write_html(report, html_path)
    write_markdown(report, md_path)

    console_print("\n" + "=" * 60)
    if report.all_passed:
        console_print("  VERDICT: ALL PASSED")
    else:
        console_print("  VERDICT: FAILURES DETECTED - see report for details")
    console_print("=" * 60)
    console_print(f"\n  HTML report: {html_path}")
    console_print(f"  Markdown:    {md_path}")
    console_print(f"\n  Open HTML in browser: file:///{html_path.as_posix()}")

    if args.open:
        webbrowser.open(html_path.as_uri())

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
