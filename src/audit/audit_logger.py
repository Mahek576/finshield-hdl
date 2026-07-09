from pathlib import Path
import json
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "final_decision_transactions.csv"
AUDIT_JSONL_PATH = PROJECT_ROOT / "results" / "audit_logs.jsonl"
AUDIT_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "audit_log_view.csv"
AUDIT_SUMMARY_PATH = PROJECT_ROOT / "results" / "audit_summary.json"


REQUIRED_COLUMNS = [
    "transaction_id",
    "account_id",
    "timestamp",
    "amount",
    "daily_limit",
    "total_after_txn",
    "risk_type",
    "is_fraud",
    "daily_limit_breach",
    "velocity_spike",
    "large_amount_anomaly",
    "new_beneficiary_risk",
    "account_takeover_signal",
    "high_merchant_risk",
    "failed_login_risk",
    "rule_risk_score",
    "rule_action",
    "reason_codes",
    "ml_fraud_score",
    "model_confidence",
    "predicted_fraud",
    "autoencoder_anomaly_score",
    "isolation_forest_anomaly_score",
    "autoencoder_reconstruction_error",
    "final_risk_score",
    "final_action",
    "final_action_code",
    "final_reason"
]


def load_final_decisions():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run src/rules/final_decision_engine.py before generating audit logs."
        )

    df = pd.read_csv(INPUT_PATH)

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


def clean_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def get_severity(final_action):
    severity_map = {
        "ALLOW": "LOW",
        "WARN": "MEDIUM",
        "BLOCK": "HIGH",
        "LOCK": "CRITICAL"
    }

    return severity_map.get(final_action, "UNKNOWN")


def get_decision_source(row):
    rule_enforced = row["rule_action"] != "ALLOW"
    rule_monitored = row["reason_codes"] != "NO_RULE_TRIGGERED"

    ml_active = (
        row["predicted_fraud"] == 1
        or row["ml_fraud_score"] >= 55
    )

    anomaly_active = (
        row["autoencoder_anomaly_score"] >= 70
        or row["isolation_forest_anomaly_score"] >= 75
    )

    if rule_enforced and ml_active and anomaly_active:
        return "ML_RULE_ANOMALY_ENGINE"

    if ml_active and anomaly_active:
        return "ML_AND_ANOMALY_ENGINE"

    if rule_enforced and anomaly_active:
        return "RULE_AND_ANOMALY_ENGINE"

    if rule_enforced and ml_active:
        return "ML_AND_RULE_ENGINE"

    if anomaly_active:
        return "ANOMALY_ENGINE"

    if ml_active:
        return "ML_ENGINE"

    if rule_enforced:
        return "RULE_ENGINE"

    if rule_monitored:
        return "RULE_ENGINE_MONITORED"

    return "NO_RISK_ENGINE_TRIGGERED"


def build_signal_snapshot(row):
    return {
        "daily_limit_breach": int(row["daily_limit_breach"]),
        "velocity_spike": int(row["velocity_spike"]),
        "large_amount_anomaly": int(row["large_amount_anomaly"]),
        "new_beneficiary_risk": int(row["new_beneficiary_risk"]),
        "account_takeover_signal": int(row["account_takeover_signal"]),
        "high_merchant_risk": int(row["high_merchant_risk"]),
        "failed_login_risk": int(row["failed_login_risk"])
    }


def build_score_snapshot(row):
    return {
        "rule_risk_score": int(row["rule_risk_score"]),
        "ml_fraud_score": int(row["ml_fraud_score"]),
        "model_confidence": int(row["model_confidence"]),
        "autoencoder_anomaly_score": int(row["autoencoder_anomaly_score"]),
        "isolation_forest_anomaly_score": int(row["isolation_forest_anomaly_score"]),
        "autoencoder_reconstruction_error": float(row["autoencoder_reconstruction_error"]),
        "final_risk_score": int(row["final_risk_score"])
    }


def build_transaction_snapshot(row):
    return {
        "account_id": clean_value(row["account_id"]),
        "amount": float(row["amount"]),
        "daily_limit": float(row["daily_limit"]),
        "total_after_txn": float(row["total_after_txn"])
    }


def build_anomaly_decision(row):
    autoencoder_score = int(row["autoencoder_anomaly_score"])
    isolation_score = int(row["isolation_forest_anomaly_score"])

    autoencoder_flag = autoencoder_score >= 70
    isolation_flag = isolation_score >= 75

    if autoencoder_score >= 85 or isolation_score >= 85:
        anomaly_severity = "HIGH"
    elif autoencoder_flag or isolation_flag:
        anomaly_severity = "MEDIUM"
    else:
        anomaly_severity = "LOW"

    return {
        "autoencoder_anomaly_score": autoencoder_score,
        "isolation_forest_anomaly_score": isolation_score,
        "autoencoder_reconstruction_error": float(row["autoencoder_reconstruction_error"]),
        "autoencoder_anomaly_flag": bool(autoencoder_flag),
        "isolation_forest_anomaly_flag": bool(isolation_flag),
        "anomaly_severity": anomaly_severity
    }


def build_audit_record(row):
    return {
        "audit_id": f"AUD_{row['transaction_id']}",
        "event_type": "TRANSACTION_RISK_DECISION",
        "transaction_id": clean_value(row["transaction_id"]),
        "timestamp": row["timestamp"].isoformat(),
        "severity": get_severity(row["final_action"]),
        "decision_source": get_decision_source(row),
        "transaction": build_transaction_snapshot(row),
        "risk_signals": build_signal_snapshot(row),
        "risk_scores": build_score_snapshot(row),
        "rule_decision": {
            "rule_action": clean_value(row["rule_action"]),
            "reason_codes": clean_value(row["reason_codes"])
        },
        "ml_decision": {
            "predicted_fraud": int(row["predicted_fraud"]),
            "ml_fraud_score": int(row["ml_fraud_score"]),
            "model_confidence": int(row["model_confidence"])
        },
        "anomaly_decision": build_anomaly_decision(row),
        "final_decision": {
            "final_action": clean_value(row["final_action"]),
            "final_action_code": int(row["final_action_code"]),
            "final_reason": clean_value(row["final_reason"])
        },
        "ground_truth": {
            "risk_type": clean_value(row["risk_type"]),
            "is_fraud": int(row["is_fraud"])
        },
        "hardware_packet_ready": True
    }


def generate_audit_logs(df):
    audit_records = []

    for _, row in df.iterrows():
        audit_records.append(build_audit_record(row))

    return audit_records


def build_audit_log_view(audit_records):
    rows = []

    for record in audit_records:
        rows.append({
            "audit_id": record["audit_id"],
            "transaction_id": record["transaction_id"],
            "timestamp": record["timestamp"],
            "severity": record["severity"],
            "decision_source": record["decision_source"],
            "amount": record["transaction"]["amount"],
            "rule_risk_score": record["risk_scores"]["rule_risk_score"],
            "ml_fraud_score": record["risk_scores"]["ml_fraud_score"],
            "model_confidence": record["risk_scores"]["model_confidence"],
            "autoencoder_anomaly_score": record["risk_scores"]["autoencoder_anomaly_score"],
            "isolation_forest_anomaly_score": record["risk_scores"]["isolation_forest_anomaly_score"],
            "autoencoder_reconstruction_error": record["risk_scores"]["autoencoder_reconstruction_error"],
            "final_risk_score": record["risk_scores"]["final_risk_score"],
            "rule_action": record["rule_decision"]["rule_action"],
            "final_action": record["final_decision"]["final_action"],
            "final_reason": record["final_decision"]["final_reason"],
            "risk_type": record["ground_truth"]["risk_type"],
            "is_fraud": record["ground_truth"]["is_fraud"]
        })

    return pd.DataFrame(rows)


def build_audit_summary(df, audit_records):
    action_counts = df["final_action"].value_counts().to_dict()

    severity_counts = {}
    decision_source_counts = {}
    anomaly_severity_counts = {}

    for record in audit_records:
        severity = record["severity"]
        decision_source = record["decision_source"]
        anomaly_severity = record["anomaly_decision"]["anomaly_severity"]

        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        decision_source_counts[decision_source] = decision_source_counts.get(decision_source, 0) + 1
        anomaly_severity_counts[anomaly_severity] = anomaly_severity_counts.get(anomaly_severity, 0) + 1

    summary = {
        "total_audit_records": int(len(audit_records)),
        "final_action_counts": {
            str(key): int(value) for key, value in action_counts.items()
        },
        "severity_counts": {
            str(key): int(value) for key, value in severity_counts.items()
        },
        "decision_source_counts": {
            str(key): int(value) for key, value in decision_source_counts.items()
        },
        "anomaly_severity_counts": {
            str(key): int(value) for key, value in anomaly_severity_counts.items()
        },
        "blocked_or_locked_transactions": int(
            df["final_action"].isin(["BLOCK", "LOCK"]).sum()
        ),
        "warned_transactions": int((df["final_action"] == "WARN").sum()),
        "allowed_transactions": int((df["final_action"] == "ALLOW").sum()),
        "autoencoder_anomaly_flags": int(
            (df["autoencoder_anomaly_score"] >= 70).sum()
        ),
        "isolation_forest_anomaly_flags": int(
            (df["isolation_forest_anomaly_score"] >= 75).sum()
        )
    }

    return summary


def save_audit_outputs(audit_records, audit_view_df, audit_summary):
    AUDIT_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(AUDIT_JSONL_PATH, "w", encoding="utf-8") as f:
        for record in audit_records:
            f.write(json.dumps(record) + "\n")

    audit_view_df.to_csv(AUDIT_CSV_PATH, index=False)

    with open(AUDIT_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=4)


def main():
    df = load_final_decisions()

    audit_records = generate_audit_logs(df)
    audit_view_df = build_audit_log_view(audit_records)
    audit_summary = build_audit_summary(df, audit_records)

    save_audit_outputs(audit_records, audit_view_df, audit_summary)

    print("Audit log generation completed successfully.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Audit JSONL path: {AUDIT_JSONL_PATH}")
    print(f"Audit CSV view path: {AUDIT_CSV_PATH}")
    print(f"Audit summary path: {AUDIT_SUMMARY_PATH}")
    print()
    print(f"Total audit records: {len(audit_records)}")
    print()
    print("Final action counts:")
    print(df["final_action"].value_counts())
    print()
    print("Severity counts:")
    print(pd.Series([record["severity"] for record in audit_records]).value_counts())
    print()
    print("Decision source counts:")
    print(pd.Series([record["decision_source"] for record in audit_records]).value_counts())
    print()
    print("Anomaly severity counts:")
    print(pd.Series([record["anomaly_decision"]["anomaly_severity"] for record in audit_records]).value_counts())
    print()
    print("Sample audit records:")
    for record in audit_records[:2]:
        print(json.dumps(record, indent=2))
        print()


if __name__ == "__main__":
    main()