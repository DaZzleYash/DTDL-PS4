"""Seed example finance rules via RuleService.

Usage:
    python -m app.finance.seed_rules
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.rules.service import RuleService
from app.schemas.rule import RuleCreate

logger = logging.getLogger(__name__)


def _years_ago(years: int) -> str:
    """Return an ISO-8601 date `years` before today (handles Feb 29)."""
    today = date.today()
    try:
        cutoff = today.replace(year=today.year - years)
    except ValueError:
        cutoff = today.replace(month=2, day=28, year=today.year - years)
    return cutoff.isoformat()


def build_example_rules() -> list[RuleCreate]:
    """Return the 5 demo rules. Underage cutoff is computed at call time."""
    adult_cutoff = _years_ago(18)
    return [
        RuleCreate(
            name="Minimum Credit Score",
            description="Approve applicants whose credit score is at least 650.",
            category="ELIGIBILITY",
            priority=10,
            active=True,
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
            decision_outcome="APPROVE",
            decision_metadata={"riskTier": "A"},
        ),
        RuleCreate(
            name="High Debt-to-Income Flag",
            description="Flag applications where debt-to-income exceeds 45% for manual review.",
            category="RISK",
            priority=20,
            active=True,
            condition={
                "type": "NUMERIC",
                "field": "risk_flags.debtToIncomeRatio",
                "operator": "GT",
                "value": 0.45,
            },
            decision_outcome="MANUAL_REVIEW",
            decision_metadata={"reason": "high_dti"},
        ),
        RuleCreate(
            name="VIP Existing Customer Fast Track",
            description="Fast-track existing customers with a strong credit score (700+).",
            category="ELIGIBILITY",
            priority=25,
            active=True,
            condition={
                "type": "AND",
                "conditions": [
                    {
                        "type": "BOOLEAN",
                        "field": "applicant.existingCustomer",
                        "operator": "EQUALS",
                        "value": True,
                    },
                    {
                        "type": "NUMERIC",
                        "field": "applicant.creditScore",
                        "operator": "GTE",
                        "value": 700,
                    },
                ],
            },
            decision_outcome="APPROVE",
            decision_metadata={"fastTrack": True},
        ),
        RuleCreate(
            name="Prior Default Block",
            description="Reject applicants who have previously defaulted.",
            category="FRAUD",
            priority=30,
            active=True,
            condition={
                "type": "BOOLEAN",
                "field": "risk_flags.hasDefaulted",
                "operator": "EQUALS",
                "value": True,
            },
            decision_outcome="REJECT",
            decision_metadata={"reason": "prior_default"},
        ),
        RuleCreate(
            name="Underage Applicant Block",
            description=(
                f"Reject applicants born after {adult_cutoff} (under 18 at seed time)."
            ),
            category="ELIGIBILITY",
            priority=40,
            active=True,
            condition={
                "type": "DATE",
                "field": "applicant.dateOfBirth",
                "operator": "AFTER",
                "value": adult_cutoff,
            },
            decision_outcome="REJECT",
            decision_metadata={"reason": "underage"},
        ),
    ]


def seed_rules(db: Session, *, skip_existing: bool = True) -> list[str]:
    """Insert example finance rules. Returns names of rules that were created."""
    service = RuleService(db)
    existing_names = {rule.name for rule in service.list()}
    created: list[str] = []

    for payload in build_example_rules():
        if skip_existing and payload.name in existing_names:
            logger.info("Skipping existing rule: %s", payload.name)
            continue
        service.create(payload)
        created.append(payload.name)
        logger.info("Seeded rule: %s", payload.name)

    return created


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    db = SessionLocal()
    try:
        created = seed_rules(db)
        if created:
            print(f"Seeded {len(created)} rule(s): {', '.join(created)}")
        else:
            print("No new rules seeded (all example rules already present).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
