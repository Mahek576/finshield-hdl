from pathlib import Path
import json
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_pipeline_outputs_exist():
    required_paths = [
        PROJECT_ROOT / "data" / "sample_transactions.csv",
        PROJECT_ROOT / "data" / "processed" / "rule_scored_transactions.csv",
        PROJECT_ROOT / "data" / "processed" / "ml_scored_transactions.csv",
        PROJECT_ROOT / "data" / "processed" / "benchmark_scored_transactions.csv",
        PROJECT_ROOT / "data" / "processed" / "final_decision_transactions.csv",
        PROJECT_ROOT / "data" / "processed" / "hardware_risk_packets.csv",
        PROJECT_ROOT / "data" / "processed" / "audit_log_view.csv",
        PROJECT_ROOT / "results" / "model_metrics.json",
        PROJECT_ROOT / "results" / "model_comparison.csv",
        PROJECT_ROOT / "results" / "best_model_summary.json",
        PROJECT_ROOT / "results" / "audit_summary.json"
    ]

    for path in required_paths:
        assert path.exists(), f"Missing expected pipeline output: {path}"


def test_final_decision_file_has_valid_action_codes():
    path = PROJECT_ROOT / "data" / "processed" / "final_decision_transactions.csv"

    df = pd.read_csv(path)

    assert "final_action" in df.columns
    assert "final_action_code" in df.columns

    valid_actions = {"ALLOW", "WARN", "BLOCK", "LOCK"}
    valid_codes = {0, 1, 2, 3}

    assert set(df["final_action"].unique()).issubset(valid_actions)
    assert set(df["final_action_code"].unique()).issubset(valid_codes)


def test_hardware_packet_contains_anomaly_fields():
    path = PROJECT_ROOT / "data" / "processed" / "hardware_risk_packets.csv"

    df = pd.read_csv(path)

    required_columns = [
        "transaction_id",
        "ml_fraud_score",
        "model_confidence",
        "autoencoder_anomaly_score",
        "isolation_forest_anomaly_score",
        "final_risk_score",
        "final_action_code"
    ]

    for column in required_columns:
        assert column in df.columns


def test_best_model_summary_has_best_model():
    path = PROJECT_ROOT / "results" / "best_model_summary.json"

    with open(path, "r", encoding="utf-8") as file:
        summary = json.load(file)

    assert "best_model_name" in summary
    assert "metrics" in summary
    assert summary["best_model_name"] != ""