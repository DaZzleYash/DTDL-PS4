"""Example loan application payloads for demos and finance tests.

Each scenario is shaped as an EvaluateRequest-compatible dict plus the
expected final_decision when run against the seeded rule set.

Priority note: Module C picks the first match in ascending priority order,
so hard-stop scenarios use a credit score below 650 so Minimum Credit Score
does not win before the intended rule.
"""

from __future__ import annotations

from datetime import date


def _years_ago(years: int) -> str:
    today = date.today()
    try:
        cutoff = today.replace(year=today.year - years)
    except ValueError:
        cutoff = today.replace(month=2, day=28, year=today.year - years)
    return cutoff.isoformat()


def _base_applicant(**overrides: object) -> dict:
    applicant = {
        "creditScore": 720,
        "annualIncome": 85000,
        "employmentStatus": "EMPLOYED",
        "dateOfBirth": _years_ago(30),
        "existingCustomer": False,
    }
    applicant.update(overrides)
    return applicant


def _base_loan(**overrides: object) -> dict:
    loan = {"amount": 25000, "purpose": "AUTO", "termMonths": 60}
    loan.update(overrides)
    return loan


def _base_risk(**overrides: object) -> dict:
    risk = {"hasDefaulted": False, "debtToIncomeRatio": 0.30}
    risk.update(overrides)
    return risk


# --- Individual scenario contexts -------------------------------------------------

APPROVE_GOOD_APPLICANT = {
    "applicant": _base_applicant(creditScore=720),
    "loan": _base_loan(),
    "risk_flags": _base_risk(),
}

MANUAL_REVIEW_HIGH_DTI = {
    "applicant": _base_applicant(creditScore=600),  # below 650 so APPROVE does not win first
    "loan": _base_loan(amount=40000, purpose="PERSONAL"),
    "risk_flags": _base_risk(debtToIncomeRatio=0.55),
}

REJECT_PRIOR_DEFAULT = {
    "applicant": _base_applicant(creditScore=600),
    "loan": _base_loan(purpose="PERSONAL"),
    "risk_flags": _base_risk(hasDefaulted=True, debtToIncomeRatio=0.30),
}

REJECT_UNDERAGE = {
    "applicant": _base_applicant(creditScore=600, dateOfBirth=_years_ago(16)),
    "loan": _base_loan(amount=5000, purpose="EDUCATION", termMonths=24),
    "risk_flags": _base_risk(),
}

APPROVE_VIP_CUSTOMER = {
    "applicant": _base_applicant(creditScore=750, existingCustomer=True),
    "loan": _base_loan(amount=50000, purpose="HOME", termMonths=120),
    "risk_flags": _base_risk(debtToIncomeRatio=0.28),
}

# EvaluateRequest-shaped payloads ready for POST /api/decisions/evaluate
SAMPLE_REQUESTS: dict[str, dict] = {
    "approve_good_applicant": {
        "context": APPROVE_GOOD_APPLICANT,
        "category": None,
    },
    "manual_review_high_dti": {
        "context": MANUAL_REVIEW_HIGH_DTI,
        "category": None,
    },
    "reject_prior_default": {
        "context": REJECT_PRIOR_DEFAULT,
        "category": None,
    },
    "reject_underage": {
        "context": REJECT_UNDERAGE,
        "category": None,
    },
    "approve_vip_customer": {
        "context": APPROVE_VIP_CUSTOMER,
        "category": None,
    },
}

# Expected final_decision for each scenario against the seeded rule set
EXPECTED_DECISIONS: dict[str, str] = {
    "approve_good_applicant": "APPROVE",
    "manual_review_high_dti": "MANUAL_REVIEW",
    "reject_prior_default": "REJECT",
    "reject_underage": "REJECT",
    "approve_vip_customer": "APPROVE",
}

# VIP also matches Minimum Credit Score; assert both appear in rules_matched
EXPECTED_MATCHED_RULE_NAMES: dict[str, set[str]] = {
    "approve_good_applicant": {"Minimum Credit Score"},
    "manual_review_high_dti": {"High Debt-to-Income Flag"},
    "reject_prior_default": {"Prior Default Block"},
    "reject_underage": {"Underage Applicant Block"},
    "approve_vip_customer": {"Minimum Credit Score", "VIP Existing Customer Fast Track"},
}
