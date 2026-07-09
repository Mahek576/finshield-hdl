import pandas as pd

from src.audit import audit_logger


def make_final_decision_row():
    return pd.Series({
        "transaction_id": "TXN_TEST_001",
        "account_id": "ACC_TEST",
        "timestamp": pd.to_datetime("2026-07-01 10:00:00"),
        "amount": 25000.0,
        "daily_limit": 50000.0,
        "total_after_txn": 60000.0,
        "risk_type": "ACCOUNT_TAKEOVER",
        "is_fraud": 1,

        "daily_limit_breach": 1,
        "velocity_spike": 1,
        "large_amount_anomaly": 1,
        "new_beneficiary_risk": 1,
        "account_takeover_signal": 1,
        "high_merchant_risk": 1,
        "failed_login_risk": 1,

        "rule_risk_score": 100,
        "rule_action": "LOCK",
        "reason_codes": "DAILY_LIMIT_BREACH|ACCOUNT_TAKEOVER_SIGNAL",

        "ml_fraud_score": 100,
        "model_confidence": 100,
        "predicted_fraud": 1,

        "autoencoder_anomaly_score": 100,
        "isolation_forest_anomaly_score": 100,
        "autoencoder_reconstruction_error": 5.5,

        "final_risk_score": 100,
        "final_action": "LOCK",
        "final_action_code": 3,
        "final_reason": "RULE_LOCK|HIGH_CONFIDENCE_ML_FRAUD|DEEP_AUTOENCODER_ANOMALY|ATO_SECURITY_OVERRIDE"
    })


def test_audit_record_contains_required_sections():
    row = make_final_decision_row()

    record = audit_logger.build_audit_record(row)

    assert record["audit_id"] == "AUD_TXN_TEST_001"
    assert record["event_type"] == "TRANSACTION_RISK_DECISION"
    assert record["severity"] == "CRITICAL"
    assert record["hardware_packet_ready"] is True

    assert "transaction" in record
    assert "risk_signals" in record
    assert "risk_scores" in record
    assert "rule_decision" in record
    assert "ml_decision" in record
    assert "anomaly_decision" in record
    assert "final_decision" in record
    assert "ground_truth" in record


def test_audit_record_tracks_anomaly_decision():
    row = make_final_decision_row()

    record = audit_logger.build_audit_record(row)
    anomaly_decision = record["anomaly_decision"]

    assert anomaly_decision["autoencoder_anomaly_score"] == 100
    assert anomaly_decision["isolation_forest_anomaly_score"] == 100
    assert anomaly_decision["autoencoder_anomaly_flag"] is True
    assert anomaly_decision["isolation_forest_anomaly_flag"] is True
    assert anomaly_decision["anomaly_severity"] == "HIGH"


def test_decision_source_detects_ml_rule_anomaly_engine():
    row = make_final_decision_row()

    decision_source = audit_logger.get_decision_source(row)

    assert decision_source == "ML_RULE_ANOMALY_ENGINE"


def test_audit_log_view_contains_anomaly_columns():
    row = make_final_decision_row()
    record = audit_logger.build_audit_record(row)

    audit_view_df = audit_logger.build_audit_log_view([record])

    assert "autoencoder_anomaly_score" in audit_view_df.columns
    assert "isolation_forest_anomaly_score" in audit_view_df.columns
    assert "autoencoder_reconstruction_error" in audit_view_df.columns
    assert audit_view_df.iloc[0]["final_action"] == "LOCK"