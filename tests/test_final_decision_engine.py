import pandas as pd

from src.rules import final_decision_engine


def make_base_scored_transaction():
    return {
        "transaction_id": "TXN_TEST_001",
        "account_id": "ACC_TEST",
        "timestamp": "2026-07-01 10:00:00",
        "amount": 1000.0,
        "daily_limit": 50000.0,
        "total_after_txn": 12000.0,
        "risk_type": "NORMAL",
        "is_fraud": 0,

        "daily_limit_breach": 0,
        "velocity_spike": 0,
        "large_amount_anomaly": 0,
        "new_beneficiary_risk": 0,
        "account_takeover_signal": 0,
        "high_merchant_risk": 0,
        "failed_login_risk": 0,

        "rule_risk_score": 0,
        "rule_action": "ALLOW",
        "rule_action_code": 0,
        "reason_codes": "NO_RULE_TRIGGERED",

        "ml_fraud_score": 5,
        "model_confidence": 95,
        "predicted_fraud": 0,

        "gradient_boosting_score": 5,
        "random_forest_score": 5,
        "logistic_regression_score": 5,
        "mlp_neural_network_score": 5,
        "isolation_forest_anomaly_score": 10,
        "autoencoder_anomaly_score": 10,
        "autoencoder_reconstruction_error": 0.1
    }


def test_low_risk_transaction_allows():
    transaction = make_base_scored_transaction()

    df = pd.DataFrame([transaction])
    final_df = final_decision_engine.apply_final_decisions(df)

    row = final_df.iloc[0]

    assert row["final_action"] == "ALLOW"
    assert row["final_action_code"] == 0
    assert row["final_risk_score"] < 65


def test_account_takeover_with_high_ml_locks():
    transaction = make_base_scored_transaction()
    transaction["account_takeover_signal"] = 1
    transaction["ml_fraud_score"] = 90
    transaction["model_confidence"] = 95
    transaction["predicted_fraud"] = 1
    transaction["rule_risk_score"] = 70
    transaction["reason_codes"] = "ACCOUNT_TAKEOVER_SIGNAL"

    df = pd.DataFrame([transaction])
    final_df = final_decision_engine.apply_final_decisions(df)

    row = final_df.iloc[0]

    assert row["final_action"] == "LOCK"
    assert row["final_action_code"] == 3
    assert "ATO_SECURITY_OVERRIDE" in row["final_reason"]


def test_high_autoencoder_and_ml_risk_locks():
    transaction = make_base_scored_transaction()
    transaction["ml_fraud_score"] = 90
    transaction["model_confidence"] = 95
    transaction["predicted_fraud"] = 1
    transaction["autoencoder_anomaly_score"] = 96
    transaction["isolation_forest_anomaly_score"] = 80

    df = pd.DataFrame([transaction])
    final_df = final_decision_engine.apply_final_decisions(df)

    row = final_df.iloc[0]

    assert row["final_action"] == "LOCK"
    assert "DEEP_AUTOENCODER_ANOMALY" in row["final_reason"]


def test_anomaly_only_transaction_warns():
    transaction = make_base_scored_transaction()
    transaction["autoencoder_anomaly_score"] = 75
    transaction["isolation_forest_anomaly_score"] = 20
    transaction["ml_fraud_score"] = 20
    transaction["rule_risk_score"] = 5

    df = pd.DataFrame([transaction])
    final_df = final_decision_engine.apply_final_decisions(df)

    row = final_df.iloc[0]

    assert row["final_action"] in ["WARN", "BLOCK", "LOCK"]
    assert "DEEP_AUTOENCODER_ANOMALY" not in row["final_reason"] or row["autoencoder_anomaly_score"] >= 85


def test_rule_block_remains_block_or_stronger():
    transaction = make_base_scored_transaction()
    transaction["rule_action"] = "BLOCK"
    transaction["rule_action_code"] = 2
    transaction["rule_risk_score"] = 70
    transaction["daily_limit_breach"] = 1
    transaction["reason_codes"] = "DAILY_LIMIT_BREACH"

    df = pd.DataFrame([transaction])
    final_df = final_decision_engine.apply_final_decisions(df)

    row = final_df.iloc[0]

    assert row["final_action"] in ["BLOCK", "LOCK"]
    assert row["final_action_code"] in [2, 3]