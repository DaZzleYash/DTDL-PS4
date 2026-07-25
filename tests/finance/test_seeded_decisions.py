"""Finance domain demo tests — Contributor D.

Each sample payload run through the seeded rule set produces the expected
final_decision. This doubles as the project's primary demo script.
"""

import pytest

from app.finance.sample_requests import (
    EXPECTED_DECISIONS,
    EXPECTED_MATCHED_RULE_NAMES,
    SAMPLE_REQUESTS,
)
from app.finance.schemas import LoanApplicationContext
from app.finance.seed_rules import build_example_rules, seed_rules
from app.schemas.decision import EvaluateRequest


def test_loan_application_context_documents_expected_shape() -> None:
    ctx = LoanApplicationContext.model_validate(
        SAMPLE_REQUESTS["approve_good_applicant"]["context"]
    )
    assert ctx.applicant.creditScore == 720
    assert ctx.risk_flags.hasDefaulted is False
    assert ctx.loan.purpose == "AUTO"


def test_build_example_rules_has_seven_named_rules() -> None:
    rules = build_example_rules()
    names = [rule.name for rule in rules]
    assert names == [
        "Minimum Credit Score",
        "Large Loan Manual Review",
        "High Debt-to-Income Flag",
        "VIP Existing Customer Fast Track",
        "Prior Default Block",
        "Unemployed Applicant Block",
        "Underage Applicant Block",
    ]
    assert [rule.decision_outcome for rule in rules] == [
        "APPROVE",
        "MANUAL_REVIEW",
        "MANUAL_REVIEW",
        "APPROVE",
        "REJECT",
        "REJECT",
        "REJECT",
    ]


def test_seed_rules_is_idempotent(db_session) -> None:
    assert seed_rules(db_session) == [
        "Minimum Credit Score",
        "Large Loan Manual Review",
        "High Debt-to-Income Flag",
        "VIP Existing Customer Fast Track",
        "Prior Default Block",
        "Unemployed Applicant Block",
        "Underage Applicant Block",
    ]
    assert seed_rules(db_session) == []


@pytest.mark.parametrize("scenario", list(SAMPLE_REQUESTS))
def test_sample_payload_produces_expected_decision(seeded_decision_service, scenario: str) -> None:
    payload = SAMPLE_REQUESTS[scenario]
    response = seeded_decision_service.evaluate(
        EvaluateRequest(context=payload["context"], category=payload["category"])
    )

    assert response.final_decision == EXPECTED_DECISIONS[scenario]
    matched_names = {trace.rule_name for trace in response.rules_matched}
    assert EXPECTED_MATCHED_RULE_NAMES[scenario] <= matched_names
    assert response.rules_evaluated  # full trace populated
    assert response.explanation
