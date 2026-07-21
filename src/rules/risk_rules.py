from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "sample_transactions.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "rule_scored_transactions.csv"
DECISION_TRACE_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "risk_decision_traces.csv"


ACTION_TO_CODE = {
    "ALLOW": 0,
    "WARN": 1,
    "BLOCK": 2,
    "LOCK": 3
}


def load_transactions():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run src/data/generate_transactions.py first."
        )

    df = pd.read_csv(INPUT_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


def add_derived_features(df):
    df = df.copy()

    if "total_after_txn" not in df.columns:
        df["total_after_txn"] = df["daily_total_before_txn"] + df["amount"]

    if "daily_limit_utilization" not in df.columns:
        df["daily_limit_utilization"] = df["total_after_txn"] / df["daily_limit"]

    if "amount_to_avg_ratio" not in df.columns:
        df["amount_to_avg_ratio"] = df["amount"] / df["avg_amount_30d"]

    if "hour_of_day" not in df.columns:
        df["hour_of_day"] = df["timestamp"].dt.hour

    return df


def add_rule_flags(df):
    df = df.copy()

    df["daily_limit_breach"] = (
        df["total_after_txn"] > df["daily_limit"]
    ).astype(int)

    df["large_amount_anomaly"] = (
        df["amount_to_avg_ratio"] >= 5.0
    ).astype(int)

    df["velocity_spike"] = (
        df["tx_count_2min"] >= 5
    ).astype(int)

    df["new_beneficiary_risk"] = (
        (df["beneficiary_age_days"] <= 7)
        & (df["amount_to_avg_ratio"] >= 3.0)
    ).astype(int)

    df["account_takeover_signal"] = (
        (df["is_new_device"] == 1)
        & (df["is_new_location"] == 1)
        & (df["failed_login_count_1h"] >= 3)
    ).astype(int)

    df["high_merchant_risk"] = (
        df["merchant_risk_score"] >= 70
    ).astype(int)

    df["suspicious_hour_activity"] = (
        (df["hour_of_day"] <= 4)
        | (df["hour_of_day"] >= 23)
    ).astype(int)

    df["failed_login_risk"] = (
        df["failed_login_count_1h"] >= 3
    ).astype(int)

    return df


def compute_rule_score(df):
    df = df.copy()

    df["rule_risk_score"] = (
        df["daily_limit_breach"] * 30
        + df["large_amount_anomaly"] * 20
        + df["velocity_spike"] * 20
        + df["new_beneficiary_risk"] * 15
        + df["account_takeover_signal"] * 30
        + df["high_merchant_risk"] * 10
        + df["suspicious_hour_activity"] * 5
        + df["failed_login_risk"] * 10
    )

    df["rule_risk_score"] = df["rule_risk_score"].clip(0, 100)

    return df


def build_reason_codes(row):
    reasons = []

    if row["daily_limit_breach"] == 1:
        reasons.append("DAILY_LIMIT_BREACH")

    if row["large_amount_anomaly"] == 1:
        reasons.append("LARGE_AMOUNT_ANOMALY")

    if row["velocity_spike"] == 1:
        reasons.append("VELOCITY_SPIKE")

    if row["new_beneficiary_risk"] == 1:
        reasons.append("NEW_BENEFICIARY_RISK")

    if row["account_takeover_signal"] == 1:
        reasons.append("ACCOUNT_TAKEOVER_SIGNAL")

    if row["high_merchant_risk"] == 1:
        reasons.append("HIGH_MERCHANT_RISK")

    if row["suspicious_hour_activity"] == 1:
        reasons.append("SUSPICIOUS_HOUR_ACTIVITY")

    if row["failed_login_risk"] == 1:
        reasons.append("FAILED_LOGIN_RISK")

    if len(reasons) == 0:
        return "NO_RULE_TRIGGERED"

    return "|".join(reasons)


def decide_action(row):
    critical_cluster_count = (
        row["daily_limit_breach"]
        + row["velocity_spike"]
        + row["new_beneficiary_risk"]
        + row["large_amount_anomaly"]
        + row["high_merchant_risk"]
    )

    if row["account_takeover_signal"] == 1 and critical_cluster_count >= 2:
        return "LOCK"

    if row["rule_risk_score"] >= 85:
        return "LOCK"

    if row["daily_limit_breach"] == 1:
        return "BLOCK"

    if row["account_takeover_signal"] == 1:
        return "BLOCK"

    if row["velocity_spike"] == 1 and critical_cluster_count >= 2:
        return "BLOCK"

    if row["new_beneficiary_risk"] == 1 and row["high_merchant_risk"] == 1:
        return "BLOCK"

    if row["large_amount_anomaly"] == 1 and row["high_merchant_risk"] == 1:
        return "BLOCK"

    if row["rule_risk_score"] >= 65:
        return "BLOCK"

    if row["velocity_spike"] == 1:
        return "WARN"

    if row["new_beneficiary_risk"] == 1:
        return "WARN"

    if row["large_amount_anomaly"] == 1:
        return "WARN"

    if row["failed_login_risk"] == 1:
        return "WARN"

    if row["rule_risk_score"] >= 35:
        return "WARN"

    return "ALLOW"

def build_risk_decision_traces(df):
    packet_columns = [
        "transaction_id",
        "daily_limit_breach",
        "velocity_spike",
        "large_amount_anomaly",
        "new_beneficiary_risk",
        "account_takeover_signal",
        "high_merchant_risk",
        "failed_login_risk",
        "rule_risk_score",
        "rule_action_code",
        "rule_action"
    ]

    packets = df[packet_columns].copy()

    return packets


def apply_rules(df):
    df = add_derived_features(df)
    df = add_rule_flags(df)
    df = compute_rule_score(df)

    df["reason_codes"] = df.apply(build_reason_codes, axis=1)
    df["rule_action"] = df.apply(decide_action, axis=1)
    df["rule_action_code"] = df["rule_action"].map(ACTION_TO_CODE)

    return df


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = load_transactions()
    scored_df = apply_rules(df)
    decision_traces_df = build_risk_decision_traces(scored_df)

    scored_df.to_csv(OUTPUT_PATH, index=False)
    decision_traces_df.to_csv(DECISION_TRACE_OUTPUT_PATH, index=False)

    print("Cybersecurity risk-rule engine completed successfully.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Scored output path: {OUTPUT_PATH}")
    print(f"Risk decision trace output path: {DECISION_TRACE_OUTPUT_PATH}")
    print()
    print(f"Rows processed: {len(scored_df)}")
    print()
    print("Rule action distribution:")
    print(scored_df["rule_action"].value_counts())
    print()
    print("Average rule risk score by true risk type:")
    print(
        scored_df.groupby("risk_type")["rule_risk_score"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )
    print()
    print("Top triggered reason codes:")
    print(scored_df["reason_codes"].value_counts().head(10))
    print()
    print("Sample decision packets:")
    print(decision_traces_df.head(10))


if __name__ == "__main__":
    main()