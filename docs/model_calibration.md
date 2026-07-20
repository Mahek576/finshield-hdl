# Model Probability Calibration

FinShield includes probability calibration utilities to evaluate and improve the reliability of fraud model probability outputs.

A fraud model should not only rank transactions correctly. It should also produce probabilities that are meaningful enough for operational risk decisions.

For example, if a group of transactions receives an average predicted fraud probability of `0.80`, then roughly 80% of those transactions should be fraudulent in a well-calibrated system.

## Why Calibration Matters

Fraud platforms use model probabilities to decide whether a transaction should be allowed, reviewed, or blocked.

Poorly calibrated probabilities can create operational problems:

| Problem | Impact |
|---|---|
| Overconfident fraud scores | Too many genuine users may be blocked |
| Underconfident fraud scores | Risky transactions may pass through |
| Unreliable probabilities | Thresholds become harder to justify |
| No calibration reporting | Model confidence becomes difficult to audit |

Calibration improves trust in downstream decisions such as:

- `ALLOW`
- `REVIEW`
- `BLOCK`

## Metrics Used

FinShield evaluates calibration using:

| Metric | Meaning |
|---|---|
| Brier Score | Mean squared error of predicted probabilities |
| Log Loss | Penalizes confident wrong predictions |
| ROC-AUC | Ranking quality between genuine and fraud transactions |
| Average Precision | Precision-recall quality for imbalanced fraud settings |
| Expected Calibration Error | Weighted average gap between predicted probability and observed fraud rate |
| Maximum Calibration Error | Largest bin-level calibration gap |

## Calibration Bins

Predicted probabilities are divided into bins.

For each bin, FinShield records:

- Bin range
- Number of transactions
- Mean predicted fraud probability
- Observed fraud rate
- Absolute calibration gap

This allows the project to show whether predicted probabilities are reliable across low-risk, medium-risk, and high-risk ranges.

## Supported Calibration Methods

FinShield supports model-agnostic probability calibration.

### Sigmoid Calibration

Uses logistic calibration on top of raw model probabilities.

This is useful when the model is systematically overconfident or underconfident.

### Isotonic Calibration

Uses a non-parametric monotonic calibration curve.

This is useful when the calibration relationship is not well represented by a simple sigmoid curve.

## Generated Outputs

The calibration module can generate:

```text
results/calibration_summary.csv
results/calibration_before_bins.csv
results/calibration_after_bins.csv

