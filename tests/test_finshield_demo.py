from pathlib import Path

import pandas as pd

from scripts.run_finshield_demo import build_demo_transaction, run_demo


def test_build_demo_transaction_contains_core_fields():
    transaction = build_demo_transaction()

    assert transaction["transaction_id"] == "TXN-DEMO-001"
    assert transaction["final_decision"] == "BLOCK"
    assert transaction["fraud_probability"] > 0.8
    assert transaction["risk_score"] > 0.8
    assert transaction["anomaly_flag"] is True


def test_run_demo_generates_expected_outputs(tmp_path):
    generated_paths = run_demo(output_dir=tmp_path)

    expected_keys = {
        "transaction_csv",
        "case_report",
        "transaction_explanation",
        "investigation_report",
        "policy_answer",
        "demo_summary",
    }

    assert set(generated_paths.keys()) == expected_keys

    for path in generated_paths.values():
        assert Path(path).exists()

    df = pd.read_csv(generated_paths["transaction_csv"])
    assert len(df) == 1
    assert df.loc[0, "final_decision"] == "BLOCK"

    case_text = Path(generated_paths["case_report"]).read_text(encoding="utf-8")
    assert "Fraud Investigation Case Report" in case_text

    explanation_text = Path(generated_paths["transaction_explanation"]).read_text(encoding="utf-8")
    assert "FinShield Analyst Explanation" in explanation_text

    investigation_text = Path(generated_paths["investigation_report"]).read_text(encoding="utf-8")
    assert "FinShield Investigation Summary" in investigation_text

    policy_text = Path(generated_paths["policy_answer"]).read_text(encoding="utf-8")
    assert "FinShield Policy-Grounded Answer" in policy_text
