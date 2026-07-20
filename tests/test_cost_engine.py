from src.risk.cost_engine import (
    CostPolicy,
    RiskDecision,
    compute_rule_severity,
    decision_from_transaction_row,
    explain_decision,
    make_cost_sensitive_decision,
)


def test_safe_low_risk_transaction_is_allowed():
    result = make_cost_sensitive_decision(
        fraud_probability=0.10,
        model_confidence=0.95,
        anomaly_flag=False,
        rule_flags={},
    )

    assert result.decision == RiskDecision.ALLOW
    assert result.adjusted_risk_score < 0.35
    assert result.rule_severity_score == 0


def test_medium_risk_transaction_goes_to_review():
    result = make_cost_sensitive_decision(
        fraud_probability=0.42,
        model_confidence=0.90,
        anomaly_flag=False,
        rule_flags={},
    )

    assert result.decision == RiskDecision.REVIEW
    assert 0.35 <= result.adjusted_risk_score < 0.75


def test_high_risk_transaction_is_blocked():
    result = make_cost_sensitive_decision(
        fraud_probability=0.82,
        model_confidence=0.88,
        anomaly_flag=False,
        rule_flags={},
    )

    assert result.decision == RiskDecision.BLOCK
    assert result.adjusted_risk_score >= 0.75


def test_anomaly_boosts_borderline_transaction_to_review():
    result = make_cost_sensitive_decision(
        fraud_probability=0.28,
        model_confidence=0.90,
        anomaly_flag=True,
        rule_flags={},
    )

    assert result.decision == RiskDecision.REVIEW
    assert result.anomaly_flag is True


def test_severe_rule_risk_can_block_transaction():
    result = make_cost_sensitive_decision(
        fraud_probability=0.40,
        model_confidence=0.90,
        anomaly_flag=False,
        rule_flags={
            "account_takeover_pattern": True,
            "multiple_failed_logins": True,
        },
    )

    assert result.rule_severity_score >= 80
    assert result.decision == RiskDecision.BLOCK


def test_rule_severity_is_capped_at_100():
    severity = compute_rule_severity(
        {
            "amount_limit_violation": True,
            "daily_limit_violation": True,
            "velocity_violation": True,
            "foreign_ip": True,
            "new_device": True,
            "multiple_failed_logins": True,
            "account_takeover_pattern": True,
            "blacklisted_merchant": True,
            "high_risk_country": True,
            "unusual_time": True,
        }
    )

    assert severity == 100


def test_custom_policy_thresholds_work():
    policy = CostPolicy(review_threshold=0.25, block_threshold=0.60)

    result = make_cost_sensitive_decision(
        fraud_probability=0.62,
        model_confidence=0.90,
        anomaly_flag=False,
        rule_flags={},
        policy=policy,
    )

    assert result.decision == RiskDecision.BLOCK


def test_explanation_contains_core_fields():
    result = make_cost_sensitive_decision(
        fraud_probability=0.82,
        model_confidence=0.80,
        anomaly_flag=True,
        rule_flags={"velocity_violation": True},
    )

    explanation = explain_decision(result)

    assert "Decision:" in explanation
    assert "Adjusted risk score:" in explanation
    assert "Reasons:" in explanation


def test_transaction_row_adapter_supports_common_columns():
    row = {
        "ml_fraud_probability": 0.66,
        "ml_confidence": 0.81,
        "anomaly_detected": True,
        "velocity_violation": True,
    }

    result = decision_from_transaction_row(row)

    assert result.decision in {RiskDecision.REVIEW, RiskDecision.BLOCK}
    assert result.anomaly_flag is True
    assert result.rule_severity_score == 25


def test_invalid_probability_is_handled_safely():
    result = make_cost_sensitive_decision(
        fraud_probability="not-a-number",
        model_confidence=None,
        anomaly_flag=False,
        rule_flags={},
    )

    assert result.decision == RiskDecision.ALLOW
    assert result.raw_fraud_probability == 0.0
