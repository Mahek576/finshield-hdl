from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)


CalibrationMethod = Literal["sigmoid", "isotonic"]


@dataclass(frozen=True)
class CalibrationBin:
    bin_index: int
    lower_bound: float
    upper_bound: float
    count: int
    mean_predicted_probability: float
    observed_fraud_rate: float
    absolute_gap: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CalibrationReport:
    sample_count: int
    positive_count: int
    negative_count: int
    brier_score: float
    log_loss: float
    roc_auc: Optional[float]
    average_precision: Optional[float]
    expected_calibration_error: float
    maximum_calibration_error: float
    bins: List[CalibrationBin]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["bins"] = [bin_result.to_dict() for bin_result in self.bins]
        return data


def _as_binary_array(values: Any) -> np.ndarray:
    arr = np.asarray(values).reshape(-1)

    if arr.size == 0:
        raise ValueError("Input array cannot be empty.")

    unique_values = set(np.unique(arr).tolist())
    if not unique_values.issubset({0, 1, False, True}):
        raise ValueError("y_true must contain binary values only: 0/1 or False/True.")

    return arr.astype(int)


def _as_probability_array(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float).reshape(-1)

    if arr.size == 0:
        raise ValueError("Probability array cannot be empty.")

    if np.isnan(arr).any() or np.isinf(arr).any():
        raise ValueError("Probability array cannot contain NaN or infinite values.")

    return np.clip(arr, 1e-9, 1.0 - 1e-9)


def _validate_same_length(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    if y_true.shape[0] != y_prob.shape[0]:
        raise ValueError(
            f"Length mismatch: y_true has {y_true.shape[0]} rows but "
            f"y_prob has {y_prob.shape[0]} rows."
        )


def evaluate_probability_calibration(
    y_true: Any,
    y_prob: Any,
    n_bins: int = 10,
) -> CalibrationReport:
    """
    Evaluate how reliable fraud probabilities are.

    A model can have high classification accuracy but poorly calibrated
    probabilities. Calibration metrics help determine whether probabilities
    can be trusted for operational ALLOW / REVIEW / BLOCK thresholds.
    """

    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")

    y_true_arr = _as_binary_array(y_true)
    y_prob_arr = _as_probability_array(y_prob)
    _validate_same_length(y_true_arr, y_prob_arr)

    sample_count = int(y_true_arr.shape[0])
    positive_count = int(y_true_arr.sum())
    negative_count = int(sample_count - positive_count)

    unique_classes = np.unique(y_true_arr)
    has_both_classes = unique_classes.size == 2

    brier = float(brier_score_loss(y_true_arr, y_prob_arr))
    ll = float(log_loss(y_true_arr, y_prob_arr, labels=[0, 1]))

    roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr)) if has_both_classes else None
    avg_precision = (
        float(average_precision_score(y_true_arr, y_prob_arr))
        if has_both_classes
        else None
    )

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins: List[CalibrationBin] = []

    weighted_gap_sum = 0.0
    max_gap = 0.0

    for bin_index in range(n_bins):
        lower = float(bin_edges[bin_index])
        upper = float(bin_edges[bin_index + 1])

        if bin_index == n_bins - 1:
            mask = (y_prob_arr >= lower) & (y_prob_arr <= upper)
        else:
            mask = (y_prob_arr >= lower) & (y_prob_arr < upper)

        count = int(mask.sum())

        if count == 0:
            mean_prob = 0.0
            observed_rate = 0.0
            gap = 0.0
        else:
            mean_prob = float(y_prob_arr[mask].mean())
            observed_rate = float(y_true_arr[mask].mean())
            gap = abs(mean_prob - observed_rate)

        weighted_gap_sum += (count / sample_count) * gap
        max_gap = max(max_gap, gap)

        bins.append(
            CalibrationBin(
                bin_index=bin_index,
                lower_bound=lower,
                upper_bound=upper,
                count=count,
                mean_predicted_probability=mean_prob,
                observed_fraud_rate=observed_rate,
                absolute_gap=float(gap),
            )
        )

    return CalibrationReport(
        sample_count=sample_count,
        positive_count=positive_count,
        negative_count=negative_count,
        brier_score=brier,
        log_loss=ll,
        roc_auc=roc_auc,
        average_precision=avg_precision,
        expected_calibration_error=float(weighted_gap_sum),
        maximum_calibration_error=float(max_gap),
        bins=bins,
    )


def calibrate_probabilities(
    y_calibration: Any,
    probabilities_for_calibration: Any,
    probabilities_to_transform: Any,
    method: CalibrationMethod = "sigmoid",
) -> np.ndarray:
    """
    Calibrate existing model probabilities.

    This function is intentionally model-agnostic. It can calibrate probabilities
    produced by Random Forest, Gradient Boosting, MLP, or any future classifier.

    method="sigmoid":
        Uses Platt-style logistic calibration.

    method="isotonic":
        Uses non-parametric isotonic calibration.
    """

    y_calib = _as_binary_array(y_calibration)
    prob_calib = _as_probability_array(probabilities_for_calibration)
    prob_target = _as_probability_array(probabilities_to_transform)

    _validate_same_length(y_calib, prob_calib)

    if np.unique(y_calib).size < 2:
        raise ValueError("Calibration labels must contain both classes: 0 and 1.")

    if method == "sigmoid":
        calibrator = LogisticRegression(solver="lbfgs")
        calibrator.fit(prob_calib.reshape(-1, 1), y_calib)
        calibrated = calibrator.predict_proba(prob_target.reshape(-1, 1))[:, 1]
    elif method == "isotonic":
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrator.fit(prob_calib, y_calib)
        calibrated = calibrator.transform(prob_target)
    else:
        raise ValueError("method must be either 'sigmoid' or 'isotonic'.")

    return np.clip(np.asarray(calibrated, dtype=float), 1e-9, 1.0 - 1e-9)


def report_to_dataframe(report: CalibrationReport) -> pd.DataFrame:
    """Convert calibration bin results into a dataframe."""

    return pd.DataFrame([bin_result.to_dict() for bin_result in report.bins])


def save_calibration_report(
    before_report: CalibrationReport,
    output_dir: str | Path = "results",
    after_report: Optional[CalibrationReport] = None,
    prefix: str = "calibration",
) -> Dict[str, Path]:
    """
    Save calibration metrics and bin-level reliability data.

    Returns a dictionary of generated file paths.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary_rows = [
        {
            "stage": "before",
            "sample_count": before_report.sample_count,
            "positive_count": before_report.positive_count,
            "negative_count": before_report.negative_count,
            "brier_score": before_report.brier_score,
            "log_loss": before_report.log_loss,
            "roc_auc": before_report.roc_auc,
            "average_precision": before_report.average_precision,
            "expected_calibration_error": before_report.expected_calibration_error,
            "maximum_calibration_error": before_report.maximum_calibration_error,
        }
    ]

    generated_paths: Dict[str, Path] = {}

    before_bins_path = output_path / f"{prefix}_before_bins.csv"
    report_to_dataframe(before_report).to_csv(before_bins_path, index=False)
    generated_paths["before_bins"] = before_bins_path

    if after_report is not None:
        summary_rows.append(
            {
                "stage": "after",
                "sample_count": after_report.sample_count,
                "positive_count": after_report.positive_count,
                "negative_count": after_report.negative_count,
                "brier_score": after_report.brier_score,
                "log_loss": after_report.log_loss,
                "roc_auc": after_report.roc_auc,
                "average_precision": after_report.average_precision,
                "expected_calibration_error": after_report.expected_calibration_error,
                "maximum_calibration_error": after_report.maximum_calibration_error,
            }
        )

        after_bins_path = output_path / f"{prefix}_after_bins.csv"
        report_to_dataframe(after_report).to_csv(after_bins_path, index=False)
        generated_paths["after_bins"] = after_bins_path

    summary_path = output_path / f"{prefix}_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    generated_paths["summary"] = summary_path

    return generated_paths


def generate_calibration_summary_text(
    report: CalibrationReport,
    label: str = "model",
) -> str:
    """Create a short human-readable summary for docs or dashboard display."""

    roc_text = "N/A" if report.roc_auc is None else f"{report.roc_auc:.4f}"
    ap_text = (
        "N/A"
        if report.average_precision is None
        else f"{report.average_precision:.4f}"
    )

    return "\n".join(
        [
            f"Calibration summary for {label}:",
            f"- Samples: {report.sample_count}",
            f"- Positives: {report.positive_count}",
            f"- Negatives: {report.negative_count}",
            f"- Brier score: {report.brier_score:.4f}",
            f"- Log loss: {report.log_loss:.4f}",
            f"- ROC-AUC: {roc_text}",
            f"- Average precision: {ap_text}",
            f"- Expected calibration error: {report.expected_calibration_error:.4f}",
            f"- Maximum calibration error: {report.maximum_calibration_error:.4f}",
        ]
    )
