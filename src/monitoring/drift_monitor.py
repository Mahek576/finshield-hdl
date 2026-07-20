from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd


AlertLevel = str


@dataclass(frozen=True)
class NumericDriftResult:
    feature_name: str
    reference_count: int
    current_count: int
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float
    reference_median: float
    current_median: float
    population_stability_index: float
    alert_level: AlertLevel

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CategoricalDriftResult:
    feature_name: str
    reference_count: int
    current_count: int
    total_variation_distance: float
    changed_categories: int
    alert_level: AlertLevel

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionDriftResult:
    decision_column: str
    reference_count: int
    current_count: int
    total_variation_distance: float
    reference_distribution: Dict[str, float]
    current_distribution: Dict[str, float]
    alert_level: AlertLevel

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MonitoringReport:
    numeric_drift: List[NumericDriftResult]
    categorical_drift: List[CategoricalDriftResult]
    decision_drift: Optional[DecisionDriftResult]
    overall_alert_level: AlertLevel
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "numeric_drift": [item.to_dict() for item in self.numeric_drift],
            "categorical_drift": [item.to_dict() for item in self.categorical_drift],
            "decision_drift": None if self.decision_drift is None else self.decision_drift.to_dict(),
            "overall_alert_level": self.overall_alert_level,
            "summary": self.summary,
        }


def _clean_numeric(values: Any) -> np.ndarray:
    series = pd.Series(values)
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return numeric.to_numpy(dtype=float)


def _safe_series(values: Any) -> pd.Series:
    return pd.Series(values).dropna()


def _alert_from_score(score: float, warn_threshold: float, alert_threshold: float) -> AlertLevel:
    if score >= alert_threshold:
        return "ALERT"
    if score >= warn_threshold:
        return "WARN"
    return "OK"


def _max_alert(levels: Iterable[AlertLevel]) -> AlertLevel:
    priority = {"OK": 0, "WARN": 1, "ALERT": 2}
    result = "OK"

    for level in levels:
        if priority.get(level, 0) > priority[result]:
            result = level

    return result


def _make_bin_edges(reference_values: np.ndarray, n_bins: int) -> np.ndarray:
    if reference_values.size == 0:
        raise ValueError("reference_values cannot be empty.")

    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")

    quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.quantile(reference_values, quantiles)
    edges = np.unique(edges)

    if edges.size < 3:
        min_value = float(np.min(reference_values))
        max_value = float(np.max(reference_values))

        if min_value == max_value:
            min_value -= 0.5
            max_value += 0.5

        edges = np.linspace(min_value, max_value, n_bins + 1)

    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def _binned_proportions(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    counts, _ = np.histogram(values, bins=edges)
    total = counts.sum()

    if total == 0:
        return np.zeros_like(counts, dtype=float)

    return counts.astype(float) / total


def population_stability_index(
    reference_values: Any,
    current_values: Any,
    n_bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    reference = _clean_numeric(reference_values)
    current = _clean_numeric(current_values)

    if reference.size == 0 or current.size == 0:
        raise ValueError("Both reference and current values must contain numeric data.")

    edges = _make_bin_edges(reference, n_bins=n_bins)

    ref_prop = _binned_proportions(reference, edges)
    cur_prop = _binned_proportions(current, edges)

    ref_prop = np.clip(ref_prop, epsilon, None)
    cur_prop = np.clip(cur_prop, epsilon, None)

    psi = np.sum((cur_prop - ref_prop) * np.log(cur_prop / ref_prop))
    return float(max(0.0, psi))


def total_variation_distance(reference_values: Any, current_values: Any) -> float:
    reference = _safe_series(reference_values).astype(str)
    current = _safe_series(current_values).astype(str)

    if reference.empty or current.empty:
        raise ValueError("Both reference and current values must contain data.")

    categories = sorted(set(reference.unique()).union(set(current.unique())))

    ref_dist = reference.value_counts(normalize=True).reindex(categories, fill_value=0.0)
    cur_dist = current.value_counts(normalize=True).reindex(categories, fill_value=0.0)

    distance = 0.5 * np.abs(ref_dist.to_numpy() - cur_dist.to_numpy()).sum()
    return float(distance)


def distribution_as_dict(values: Any) -> Dict[str, float]:
    series = _safe_series(values).astype(str)

    if series.empty:
        return {}

    return {
        str(key): float(value)
        for key, value in series.value_counts(normalize=True).sort_index().items()
    }


def evaluate_numeric_feature_drift(
    reference_values: Any,
    current_values: Any,
    feature_name: str,
    n_bins: int = 10,
    warn_threshold: float = 0.10,
    alert_threshold: float = 0.25,
) -> NumericDriftResult:
    reference = _clean_numeric(reference_values)
    current = _clean_numeric(current_values)

    if reference.size == 0 or current.size == 0:
        raise ValueError(f"Feature '{feature_name}' does not contain enough numeric data.")

    psi = population_stability_index(reference, current, n_bins=n_bins)
    alert = _alert_from_score(psi, warn_threshold, alert_threshold)

    return NumericDriftResult(
        feature_name=feature_name,
        reference_count=int(reference.size),
        current_count=int(current.size),
        reference_mean=float(np.mean(reference)),
        current_mean=float(np.mean(current)),
        reference_std=float(np.std(reference)),
        current_std=float(np.std(current)),
        reference_median=float(np.median(reference)),
        current_median=float(np.median(current)),
        population_stability_index=psi,
        alert_level=alert,
    )


def evaluate_categorical_feature_drift(
    reference_values: Any,
    current_values: Any,
    feature_name: str,
    warn_threshold: float = 0.10,
    alert_threshold: float = 0.25,
) -> CategoricalDriftResult:
    reference = _safe_series(reference_values).astype(str)
    current = _safe_series(current_values).astype(str)

    if reference.empty or current.empty:
        raise ValueError(f"Feature '{feature_name}' does not contain enough categorical data.")

    distance = total_variation_distance(reference, current)
    alert = _alert_from_score(distance, warn_threshold, alert_threshold)

    categories = set(reference.unique()).union(set(current.unique()))
    ref_dist = reference.value_counts(normalize=True)
    cur_dist = current.value_counts(normalize=True)

    changed_categories = 0
    for category in categories:
        if abs(float(ref_dist.get(category, 0.0)) - float(cur_dist.get(category, 0.0))) > 0.05:
            changed_categories += 1

    return CategoricalDriftResult(
        feature_name=feature_name,
        reference_count=int(reference.shape[0]),
        current_count=int(current.shape[0]),
        total_variation_distance=distance,
        changed_categories=int(changed_categories),
        alert_level=alert,
    )


def evaluate_decision_drift(
    reference_decisions: Any,
    current_decisions: Any,
    decision_column: str = "final_decision",
    warn_threshold: float = 0.10,
    alert_threshold: float = 0.25,
) -> DecisionDriftResult:
    reference = _safe_series(reference_decisions).astype(str)
    current = _safe_series(current_decisions).astype(str)

    if reference.empty or current.empty:
        raise ValueError("Decision columns must contain data.")

    distance = total_variation_distance(reference, current)
    alert = _alert_from_score(distance, warn_threshold, alert_threshold)

    return DecisionDriftResult(
        decision_column=decision_column,
        reference_count=int(reference.shape[0]),
        current_count=int(current.shape[0]),
        total_variation_distance=distance,
        reference_distribution=distribution_as_dict(reference),
        current_distribution=distribution_as_dict(current),
        alert_level=alert,
    )


def generate_monitoring_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    numeric_features: Optional[Sequence[str]] = None,
    categorical_features: Optional[Sequence[str]] = None,
    decision_column: Optional[str] = "final_decision",
    n_bins: int = 10,
) -> MonitoringReport:
    numeric_results: List[NumericDriftResult] = []
    categorical_results: List[CategoricalDriftResult] = []

    for feature in list(numeric_features or []):
        if feature in reference_df.columns and feature in current_df.columns:
            numeric_results.append(
                evaluate_numeric_feature_drift(
                    reference_df[feature],
                    current_df[feature],
                    feature_name=feature,
                    n_bins=n_bins,
                )
            )

    for feature in list(categorical_features or []):
        if feature in reference_df.columns and feature in current_df.columns:
            categorical_results.append(
                evaluate_categorical_feature_drift(
                    reference_df[feature],
                    current_df[feature],
                    feature_name=feature,
                )
            )

    decision_result: Optional[DecisionDriftResult] = None
    if decision_column and decision_column in reference_df.columns and decision_column in current_df.columns:
        decision_result = evaluate_decision_drift(
            reference_df[decision_column],
            current_df[decision_column],
            decision_column=decision_column,
        )

    alert_levels: List[AlertLevel] = [
        item.alert_level for item in numeric_results + categorical_results
    ]

    if decision_result is not None:
        alert_levels.append(decision_result.alert_level)

    overall_alert = _max_alert(alert_levels)
    alert_count = sum(1 for level in alert_levels if level == "ALERT")
    warn_count = sum(1 for level in alert_levels if level == "WARN")

    summary = (
        f"Monitoring report completed with overall status {overall_alert}. "
        f"Alerts: {alert_count}. Warnings: {warn_count}. "
        f"Numeric features checked: {len(numeric_results)}. "
        f"Categorical features checked: {len(categorical_results)}."
    )

    return MonitoringReport(
        numeric_drift=numeric_results,
        categorical_drift=categorical_results,
        decision_drift=decision_result,
        overall_alert_level=overall_alert,
        summary=summary,
    )


def monitoring_report_to_frames(report: MonitoringReport) -> Dict[str, pd.DataFrame]:
    frames = {
        "numeric_drift": pd.DataFrame([item.to_dict() for item in report.numeric_drift]),
        "categorical_drift": pd.DataFrame([item.to_dict() for item in report.categorical_drift]),
        "decision_drift": pd.DataFrame(
            [] if report.decision_drift is None else [report.decision_drift.to_dict()]
        ),
        "summary": pd.DataFrame(
            [
                {
                    "overall_alert_level": report.overall_alert_level,
                    "summary": report.summary,
                }
            ]
        ),
    }

    return frames


def save_monitoring_report(
    report: MonitoringReport,
    output_dir: str | Path = "results",
    prefix: str = "monitoring",
) -> Dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    frames = monitoring_report_to_frames(report)
    generated_paths: Dict[str, Path] = {}

    for name, frame in frames.items():
        file_path = output_path / f"{prefix}_{name}.csv"
        frame.to_csv(file_path, index=False)
        generated_paths[name] = file_path

    return generated_paths


def generate_monitoring_summary_text(report: MonitoringReport) -> str:
    lines = [
        "Model monitoring summary:",
        f"- Overall status: {report.overall_alert_level}",
        f"- Numeric features checked: {len(report.numeric_drift)}",
        f"- Categorical features checked: {len(report.categorical_drift)}",
    ]

    if report.decision_drift is not None:
        lines.append(
            "- Decision distribution drift: "
            f"{report.decision_drift.total_variation_distance:.4f} "
            f"({report.decision_drift.alert_level})"
        )

    alerts = [
        item.feature_name
        for item in report.numeric_drift + report.categorical_drift
        if item.alert_level == "ALERT"
    ]

    warnings = [
        item.feature_name
        for item in report.numeric_drift + report.categorical_drift
        if item.alert_level == "WARN"
    ]

    if alerts:
        lines.append(f"- Alert features: {', '.join(alerts)}")
    if warnings:
        lines.append(f"- Warning features: {', '.join(warnings)}")
    if not alerts and not warnings and (
        report.decision_drift is None or report.decision_drift.alert_level == "OK"
    ):
        lines.append("- No major drift detected.")

    return "\n".join(lines)
