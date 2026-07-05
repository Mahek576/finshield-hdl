from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ml_scored_transactions.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "final_decision_transactions.csv"
HARDWARE_PACKET_PATH = PROJECT_ROOT / "data" / "processed" / "hardware_risk_packets.csv"


ACTION_TO_CODE = {
    "ALLOW": 0,
    "WARN": 1,
    "BLOCK": 2,
    "LOCK": 3
}


def load_ml_scored_transactions():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run src/ml/train_model.py before running the final decision engine."
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = [
        "transaction_id",
        "account_id",
        "amount",
        "daily_limit",
        "total_after_txn",
        "daily_limit_breach",
        "velocity_spike",
        "large_amount_anomaly",
        "new_beneficiary_risk",
        "account_takeover_signal",
        "high_merchant_risk",
        "failed_login_risk",
        "rule_risk_score",
        "rule_action",
        "rule_action_code",
        "reason_codes",
        "ml_fraud_score",
        "model_confidence",
        "predicted_fraud"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return df


def compute_final_risk_score(row):
    rule_score = row["rule_risk_score"]
    ml_score = row["ml_fraud_score"]
    confidence = row["model_confidence"]

    if confidence >= 75:
        final_score = (0.55 * ml_score) + (0.45 * rule_score)
    elif confidence >= 55:
        final_score = (0.40 * ml_score) + (0.60 * rule_score)
    else:
        final_score = (0.25 * ml_score) + (0.75 * rule_score)

    if row["account_takeover_signal"] == 1:
        final_score += 15

    if row["daily_limit_breach"] == 1:
        final_score += 10

    if row["velocity_spike"] == 1 and row["new_beneficiary_risk"] == 1:
        final_score += 10

    final_score = max(0, min(100, round(final_score)))

    return int(final_score)


def build_final_reason(row):
    reasons = []

    if row["final_action"] == "ALLOW":
        if row["reason_codes"] != "NO_RULE_TRIGGERED":
            return f"LOW_RISK_SIGNAL_MONITORED|{row['reason_codes']}"
        return "NO_RISK_SIGNAL"

    if row["rule_action"] != "ALLOW":
        reasons.append(f"RULE_{row['rule_action']}")

    if row["reason_codes"] != "NO_RULE_TRIGGERED":
        reasons.append(row["reason_codes"])

    if row["ml_fraud_score"] >= 85 and row["model_confidence"] >= 75:
        reasons.append("HIGH_CONFIDENCE_ML_FRAUD")

    if row["ml_fraud_score"] >= 70 and row["model_confidence"] < 70:
        reasons.append("HIGH_RISK_LOW_CONFIDENCE")

    if row["predicted_fraud"] == 1:
        reasons.append("ML_PREDICTED_FRAUD")

    if row["account_takeover_signal"] == 1:
        reasons.append("ATO_SECURITY_OVERRIDE")

    if len(reasons) == 0:
        return "RISK_ESCALATION_BY_FINAL_ENGINE"

    deduped_reasons = []

    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)

    return "|".join(deduped_reasons)

def decide_final_action(row):
    if row["rule_action"] == "LOCK":
        return "LOCK"

    if row["account_takeover_signal"] == 1 and row["ml_fraud_score"] >= 70:
        return "LOCK"

    if row["final_risk_score"] >= 90:
        return "LOCK"

    if row["rule_action"] == "BLOCK":
        return "BLOCK"

    if row["ml_fraud_score"] >= 90 and row["model_confidence"] >= 80:
        return "BLOCK"

    if row["ml_fraud_score"] >= 75 and row["rule_risk_score"] >= 35:
        return "BLOCK"

    if row["daily_limit_breach"] == 1:
        return "BLOCK"

    if row["final_risk_score"] >= 65:
        return "BLOCK"

    if row["rule_action"] == "WARN":
        return "WARN"

    if row["ml_fraud_score"] >= 55:
        return "WARN"

    if row["model_confidence"] < 60 and row["ml_fraud_score"] >= 40:
        return "WARN"

    return "ALLOW"


def build_hardware_packets(df):
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
        "ml_fraud_score",
        "model_confidence",
        "final_risk_score",
        "final_action_code",
        "final_action"
    ]

    packets = df[packet_columns].copy()

    return packets

def apply_final_decisions(df):
    df = df.copy()

    df["final_risk_score"] = df.apply(compute_final_risk_score, axis=1)
    df["final_action"] = df.apply(decide_final_action, axis=1)
    df["final_action_code"] = df["final_action"].map(ACTION_TO_CODE)
    df["final_reason"] = df.apply(build_final_reason, axis=1)

    return df


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = load_ml_scored_transactions()
    final_df = apply_final_decisions(df)
    packets_df = build_hardware_packets(final_df)

    final_df.to_csv(OUTPUT_PATH, index=False)
    packets_df.to_csv(HARDWARE_PACKET_PATH, index=False)

    print("Hybrid ML + cybersecurity final decision engine completed successfully.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Final decision output path: {OUTPUT_PATH}")
    print(f"Hardware packet output path: {HARDWARE_PACKET_PATH}")
    print()
    print(f"Rows processed: {len(final_df)}")
    print()
    print("Final action distribution:")
    print(final_df["final_action"].value_counts())
    print()
    print("Final action distribution by true risk type:")
    print(
        pd.crosstab(
            final_df["risk_type"],
            final_df["final_action"],
            normalize="index"
        ).round(3)
    )
    print()
    print("Average ML, rule, and final scores by risk type:")
    print(
        final_df.groupby("risk_type")[
            ["ml_fraud_score", "rule_risk_score", "final_risk_score"]
        ].mean().round(2).sort_values(
            "final_risk_score",
            ascending=False
        )
    )
    print()
    print("Sample final decisions:")
    print(
        final_df[
            [
                "transaction_id",
                "risk_type",
                "is_fraud",
                "ml_fraud_score",
                "model_confidence",
                "rule_action",
                "final_risk_score",
                "final_action",
                "final_reason"
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()