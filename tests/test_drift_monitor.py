import pandas as pd
import pytest

from src.monitoring.drift_monitor import (
    evaluate_categorical_feature_drift,
    evaluate_decision_drift,
    evaluate_numeric_feature_drift,
    generate_monitoring_report,
    generate_monitoring_summary_text,
    population_stability_index,
    save_monitoring_report,
    total_variation_distance,
)


def test_population_stability_index_detects_numeric_shift():
    reference = [100, 110, 120, 130, 140, 150, 160, 170]
    current = [500, 520, 540, 560, 580, 600, 620, 640]

    psi = population_stability_index(reference, current, n_bins=4)

    assert psi > 0.25


def test_numeric_feature_drift_returns_alert_for_large_shift():
    result = evaluate_numeric_feature_drift(
        reference_values=[10, 11, 12, 13, 14, 15],
        current_values=[80, 82, 84, 86, 88, 90],
        feature_name="transaction_amount",
        n_bins=3,
    )

    assert result.feature_name == "transaction_amount"
    assert result.alert_level == "ALERT"
    assert result.population_stability_index >= 0.25


def test_total_variation_distance_detects_category_shift():
    reference = ["ALLOW", "ALLOW", "REVIEW", "BLOCK"]
    current = ["BLOCK", "BLOCK", "BLOCK", "REVIEW"]

    distance = total_variation_distance(reference, current)

    assert distance > 0.25


def test_categorical_feature_drift_returns_result():
    result = evaluate_categorical_feature_drift(
        reference_values=["upi", "card", "card", "wallet"],
        current_values=["crypto", "crypto", "wallet", "wallet"],
        feature_name="merchant_category",
    )

    assert result.feature_name == "merchant_category"
    assert result.total_variation_distance >= 0
    assert result.alert_level in {"OK", "WARN", "ALERT"}


def test_decision_drift_detects_distribution_change():
    result = evaluate_decision_drift(
        reference_decisions=["ALLOW", "ALLOW", "ALLOW", "REVIEW", "BLOCK"],
        current_decisions=["BLOCK", "BLOCK", "REVIEW", "REVIEW", "REVIEW"],
    )

    assert result.decision_column == "final_decision"
    assert result.alert_level in {"WARN", "ALERT"}
    assert "ALLOW" in result.reference_distribution
    assert "BLOCK" in result.current_distribution


def test_generate_monitoring_report_combines_results():
    reference_df = pd.DataFrame(
        {
            "transaction_amount": [100, 120, 130, 140, 160, 180],
            "risk_score": [0.10, 0.20, 0.25, 0.30, 0.35, 0.40],
            "merchant_category": ["food", "food", "travel", "shopping", "food", "travel"],
            "final_decision": ["ALLOW", "ALLOW", "ALLOW", "REVIEW", "REVIEW", "BLOCK"],
        }
    )

    current_df = pd.DataFrame(
        {
            "transaction_amount": [900, 950, 1000, 1100, 1200, 1300],
            "risk_score": [0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
            "merchant_category": ["crypto", "crypto", "gaming", "gaming", "travel", "crypto"],
            "final_decision": ["REVIEW", "BLOCK", "BLOCK", "BLOCK", "REVIEW", "BLOCK"],
        }
    )

    report = generate_monitoring_report(
        reference_df=reference_df,
        current_df=current_df,
        numeric_features=["transaction_amount", "risk_score"],
        categorical_features=["merchant_category"],
        decision_column="final_decision",
        n_bins=3,
    )

    assert report.overall_alert_level in {"WARN", "ALERT"}
    assert len(report.numeric_drift) == 2
    assert len(report.categorical_drift) == 1
    assert report.decision_drift is not None


def test_save_monitoring_report_writes_csv_files(tmp_path):
    reference_df = pd.DataFrame(
        {
            "amount": [10, 11, 12, 13],
            "final_decision": ["ALLOW", "ALLOW", "REVIEW", "BLOCK"],
        }
    )
    current_df = pd.DataFrame(
        {
            "amount": [50, 55, 60, 65],
            "final_decision": ["BLOCK", "BLOCK", "REVIEW", "REVIEW"],
        }
    )

    report = generate_monitoring_report(
        reference_df=reference_df,
        current_df=current_df,
        numeric_features=["amount"],
        decision_column="final_decision",
        n_bins=2,
    )

    paths = save_monitoring_report(report, output_dir=tmp_path, prefix="unit_monitoring")

    assert paths["numeric_drift"].exists()
    assert paths["decision_drift"].exists()
    assert paths["summary"].exists()


def test_monitoring_summary_text_contains_status():
    reference_df = pd.DataFrame({"amount": [10, 11, 12], "final_decision": ["ALLOW", "ALLOW", "REVIEW"]})
    current_df = pd.DataFrame({"amount": [10, 12, 13], "final_decision": ["ALLOW", "REVIEW", "REVIEW"]})

    report = generate_monitoring_report(
        reference_df=reference_df,
        current_df=current_df,
        numeric_features=["amount"],
        decision_column="final_decision",
        n_bins=2,
    )

    text = generate_monitoring_summary_text(report)

    assert "Model monitoring summary:" in text
    assert "Overall status:" in text


def test_empty_numeric_feature_raises_error():
    with pytest.raises(ValueError):
        evaluate_numeric_feature_drift(
            reference_values=[None, None],
            current_values=[1, 2, 3],
            feature_name="amount",
        )
