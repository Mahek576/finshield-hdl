import pandas as pd

from src.rules import risk_rules


def make_base_transaction():
    return {
        "transaction_id": "TXN_TEST_001",
        "account_id": "ACC_TEST",
        "timestamp": "2026-07-01 10:00:00",
        "amount": 1000.0,
        "daily_total_before_txn": 10000.0,
        "daily_limit": 50000.0,
        "tx_count_2min": 1,
        "beneficiary_age_days": 100,
        "is_new_device": 0,
        "is_new_location": 0,
        "failed_login_count_1h": 0,
        "hour_of_day": 10,
        "merchant_risk_score": 20,
        "account_age_days": 500,
        "avg_amount_30d": 1200.0,
        "risk_type": "NORMAL",
        "is_fraud": 0
    }


def test_daily_limit_breach_triggers_block():
    transaction = make_base_transaction()
    transaction["amount"] = 60000.0
    transaction["daily_total_before_txn"] = 10000.0
    transaction["daily_limit"] = 50000.0

    df = pd.DataFrame([transaction])
    scored_df = risk_rules.apply_rules(df)

    row = scored_df.iloc[0]

    assert row["daily_limit_breach"] == 1
    assert row["rule_action"] in ["BLOCK", "LOCK"]
    assert "DAILY_LIMIT_BREACH" in row["reason_codes"]


def test_velocity_spike_triggers_warn_or_stronger():
    transaction = make_base_transaction()
    transaction["tx_count_2min"] = 6

    df = pd.DataFrame([transaction])
    scored_df = risk_rules.apply_rules(df)

    row = scored_df.iloc[0]

    assert row["velocity_spike"] == 1
    assert row["rule_action"] in ["WARN", "BLOCK", "LOCK"]
    assert "VELOCITY_SPIKE" in row["reason_codes"]


def test_account_takeover_signal_triggers_block_or_lock():
    transaction = make_base_transaction()
    transaction["is_new_device"] = 1
    transaction["is_new_location"] = 1
    transaction["failed_login_count_1h"] = 4

    df = pd.DataFrame([transaction])
    scored_df = risk_rules.apply_rules(df)

    row = scored_df.iloc[0]

    assert row["account_takeover_signal"] == 1
    assert row["rule_action"] in ["BLOCK", "LOCK"]
    assert "ACCOUNT_TAKEOVER_SIGNAL" in row["reason_codes"]


def test_normal_transaction_is_allowed():
    transaction = make_base_transaction()

    df = pd.DataFrame([transaction])
    scored_df = risk_rules.apply_rules(df)

    row = scored_df.iloc[0]

    assert row["daily_limit_breach"] == 0
    assert row["velocity_spike"] == 0
    assert row["account_takeover_signal"] == 0
    assert row["rule_action"] == "ALLOW"