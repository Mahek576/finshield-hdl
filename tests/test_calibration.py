import numpy as np
import pandas as pd
import pytest

from src.ml.calibration import (
    calibrate_probabilities,
    evaluate_probability_calibration,
    generate_calibration_summary_text,
    report_to_dataframe,
    save_calibration_report,
)


def test_evaluate_probability_calibration_returns_expected_fields():
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_prob = np.array([0.05, 0.20, 0.70, 0.90, 0.30, 0.80])

    report = evaluate_probability_calibration(y_true, y_prob, n_bins=5)

    assert report.sample_count == 6
    assert report.positive_count == 3
    assert report.negative_count == 3
    assert 0 <= report.brier_score <= 1
    assert report.log_loss > 0
    assert report.roc_auc is not None
    assert report.average_precision is not None
    assert 0 <= report.expected_calibration_error <= 1
    assert len(report.bins) == 5


def test_sigmoid_calibration_outputs_valid_probabilities():
    y_calib = np.array([0, 0, 0, 1, 1, 1])
    prob_calib = np.array([0.05, 0.15, 0.25, 0.70, 0.80, 0.95])
    prob_target = np.array([0.10, 0.40, 0.90])

    calibrated = calibrate_probabilities(
        y_calibration=y_calib,
        probabilities_for_calibration=prob_calib,
        probabilities_to_transform=prob_target,
        method="sigmoid",
    )

    assert calibrated.shape == prob_target.shape
    assert np.all(calibrated > 0)
    assert np.all(calibrated < 1)


def test_isotonic_calibration_outputs_valid_probabilities():
    y_calib = np.array([0, 0, 0, 1, 1, 1])
    prob_calib = np.array([0.05, 0.15, 0.25, 0.70, 0.80, 0.95])
    prob_target = np.array([0.10, 0.40, 0.90])

    calibrated = calibrate_probabilities(
        y_calibration=y_calib,
        probabilities_for_calibration=prob_calib,
        probabilities_to_transform=prob_target,
        method="isotonic",
    )

    assert calibrated.shape == prob_target.shape
    assert np.all(calibrated > 0)
    assert np.all(calibrated < 1)


def test_report_to_dataframe_has_one_row_per_bin():
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.2, 0.8, 0.9]

    report = evaluate_probability_calibration(y_true, y_prob, n_bins=4)
    df = report_to_dataframe(report)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert "observed_fraud_rate" in df.columns


def test_save_calibration_report_writes_files(tmp_path):
    y_true = [0, 0, 1, 1, 1]
    y_prob = [0.1, 0.2, 0.7, 0.8, 0.9]

    report = evaluate_probability_calibration(y_true, y_prob, n_bins=5)
    paths = save_calibration_report(
        before_report=report,
        output_dir=tmp_path,
        prefix="unit_test_calibration",
    )

    assert paths["summary"].exists()
    assert paths["before_bins"].exists()


def test_generate_calibration_summary_text_contains_metrics():
    y_true = [0, 0, 1, 1]
    y_prob = [0.1, 0.2, 0.8, 0.9]

    report = evaluate_probability_calibration(y_true, y_prob, n_bins=4)
    text = generate_calibration_summary_text(report, label="test model")

    assert "Calibration summary for test model" in text
    assert "Brier score" in text
    assert "Expected calibration error" in text


def test_invalid_probability_input_raises_error():
    with pytest.raises(ValueError):
        evaluate_probability_calibration(
            y_true=[0, 1],
            y_prob=[0.2, float("nan")],
        )


def test_single_class_calibration_training_raises_error():
    with pytest.raises(ValueError):
        calibrate_probabilities(
            y_calibration=[0, 0, 0],
            probabilities_for_calibration=[0.1, 0.2, 0.3],
            probabilities_to_transform=[0.4, 0.5],
            method="sigmoid",
        )
