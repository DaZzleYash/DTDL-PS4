"""Decision evaluation algorithm tests — Contributor C."""

from app.decisions.service import DecisionEngineService
from app.schemas.decision import EvaluateRequest
from tests.decisions.conftest import SAMPLE_CONTEXT, FakeRuleRepository, make_rule


def test_highest_priority_match_wins_as_final_decision() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Minimum Credit Score",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
        ),
        make_rule(
            rule_id=2,
            name="High DTI",
            priority=20,
            decision_outcome="MANUAL_REVIEW",
            condition={
                "type": "NUMERIC",
                "field": "risk_flags.debtToIncomeRatio",
                "operator": "GT",
                "value": 0.25,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(EvaluateRequest(context=SAMPLE_CONTEXT))

    assert response.final_decision == "APPROVE"
    assert response.matched_decisions == ["APPROVE", "MANUAL_REVIEW"]
    assert len(response.rules_matched) == 2
    assert response.rules_matched[0].rule_name == "Minimum Credit Score"


def test_multiple_matches_are_reported() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Employed Applicant",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "STRING",
                "field": "applicant.employmentStatus",
                "operator": "EQUALS",
                "value": "EMPLOYED",
            },
        ),
        make_rule(
            rule_id=2,
            name="Low DTI",
            priority=20,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "risk_flags.debtToIncomeRatio",
                "operator": "LTE",
                "value": 0.4,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(EvaluateRequest(context=SAMPLE_CONTEXT))

    assert response.final_decision == "APPROVE"
    assert response.matched_decisions == ["APPROVE"]
    assert len(response.rules_matched) == 2
    assert "Additional matches" in response.explanation


def test_no_match_returns_no_decision() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Very High Credit Score",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 800,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(EvaluateRequest(context=SAMPLE_CONTEXT))

    assert response.final_decision == "NO_DECISION"
    assert response.matched_decisions == []
    assert response.rules_matched == []
    assert len(response.rules_rejected) == 1
    assert "No rules matched" in response.explanation


def test_malformed_rule_does_not_break_other_rules() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Broken Rule",
            priority=5,
            decision_outcome="REJECT",
            condition_json="not-valid-json",
        ),
        make_rule(
            rule_id=2,
            name="Minimum Credit Score",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(EvaluateRequest(context=SAMPLE_CONTEXT))

    assert response.final_decision == "APPROVE"
    assert len(response.rules_evaluated) == 2
    assert response.rules_rejected[0].rule_name == "Broken Rule"
    assert "Skipped" in response.rules_rejected[0].explanation
    assert response.rules_matched[0].rule_name == "Minimum Credit Score"


def test_invalid_condition_is_skipped_without_failing_request() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Unknown Type Rule",
            priority=5,
            decision_outcome="REJECT",
            condition={"type": "UNKNOWN", "field": "applicant.creditScore"},
        ),
        make_rule(
            rule_id=2,
            name="Minimum Credit Score",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(EvaluateRequest(context=SAMPLE_CONTEXT))

    assert response.final_decision == "APPROVE"
    assert "Skipped" in response.rules_rejected[0].explanation


def test_category_filter_limits_evaluated_rules() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Eligibility Rule",
            priority=10,
            decision_outcome="APPROVE",
            category="ELIGIBILITY",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
        ),
        make_rule(
            rule_id=2,
            name="Risk Rule",
            priority=20,
            decision_outcome="MANUAL_REVIEW",
            category="RISK",
            condition={
                "type": "NUMERIC",
                "field": "risk_flags.debtToIncomeRatio",
                "operator": "GT",
                "value": 0.25,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))

    response = service.evaluate(
        EvaluateRequest(context=SAMPLE_CONTEXT, category="ELIGIBILITY")
    )

    assert response.final_decision == "APPROVE"
    assert len(response.rules_evaluated) == 1
    assert response.rules_evaluated[0].rule_name == "Eligibility Rule"


def test_evaluate_bulk_returns_one_response_per_request() -> None:
    rules = [
        make_rule(
            rule_id=1,
            name="Minimum Credit Score",
            priority=10,
            decision_outcome="APPROVE",
            condition={
                "type": "NUMERIC",
                "field": "applicant.creditScore",
                "operator": "GTE",
                "value": 650,
            },
        ),
    ]
    service = DecisionEngineService(FakeRuleRepository(rules))
    requests = [
        EvaluateRequest(context=SAMPLE_CONTEXT),
        EvaluateRequest(context={"applicant": {"creditScore": 500}}),
    ]

    responses = service.evaluate_bulk(requests)

    assert len(responses) == 2
    assert responses[0].final_decision == "APPROVE"
    assert responses[1].final_decision == "NO_DECISION"
