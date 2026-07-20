# FinShield Results

This document summarizes the current performance and system behavior of FinShield.

The current pipeline includes synthetic transaction generation, cybersecurity rule scoring, supervised ML fraud detection, model benchmarking, anomaly detection, anomaly-aware final decisions, audit logging, and dashboard-ready outputs.

---

## Dataset Summary

The synthetic transaction generator created:

- Total transactions: 6000
- Normal transactions: 4652
- Fraud/risky transactions: 1348

Risk type distribution:

| Risk Type | Count |
|---|---:|
| NORMAL | 4141 |
| HIGH_AMOUNT_RISK | 280 |
| BENIGN_HIGH_VALUE | 279 |
| VELOCITY_SPIKE | 244 |
| SUBTLE_FRAUD | 242 |
| BENIGN_VELOCITY | 232 |
| RISKY_BENEFICIARY | 219 |
| ACCOUNT_TAKEOVER | 204 |
| MIXED_RISK | 159 |

The dataset includes realistic overlap between legitimate and suspicious behavior.

Examples:

- A genuine customer may perform a large transfer.
- A normal user may create a short-term velocity spike.
- Some fraud cases may appear subtle and avoid obvious hard-rule triggers.

This makes the dataset more useful for testing a real risk pipeline than a perfectly separated synthetic dataset.

---

## Cybersecurity Rule Engine Results

The rule engine applies deterministic security checks before the final decision stage.

Rule action distribution:

| Rule Action | Count |
|---|---:|
| ALLOW | 4557 |
| WARN | 577 |
| BLOCK | 547 |
| LOCK | 319 |

Average rule risk score by risk type:

| Risk Type | Average Rule Risk Score |
|---|---:|
| MIXED_RISK | 92.39 |
| ACCOUNT_TAKEOVER | 83.33 |
| HIGH_AMOUNT_RISK | 52.61 |
| RISKY_BENEFICIARY | 42.56 |
| VELOCITY_SPIKE | 23.14 |
| BENIGN_VELOCITY | 21.31 |
| BENIGN_HIGH_VALUE | 9.71 |
| SUBTLE_FRAUD | 3.35 |
| NORMAL | 1.26 |

This shows that the rule engine is strict for clear security violations but does not blindly block every suspicious-looking transaction.

That distinction is important for fintech systems because false positives can create customer friction.

---

## Primary ML Fraud Model Results

Primary model:

```text
Random Forest Classifier
```

Metrics:

| Metric | Value |
|---|---:|
| Accuracy | 0.9933 |
| Precision | 0.9739 |
| Recall | 0.9970 |
| F1 Score | 0.9853 |
| ROC AUC | 0.9996 |
| Average Precision / PR-AUC | 0.9987 |

Confusion matrix:

| Outcome | Count |
|---|---:|
| True Negative | 1154 |
| False Positive | 9 |
| False Negative | 1 |
| True Positive | 336 |

The model is strong, but not artificially perfect. That is better for a synthetic risk system because it shows the dataset contains some ambiguity.

---

## Feature Importance

Top model features:

1. merchant_risk_score
2. amount_to_avg_ratio
3. beneficiary_age_days
4. daily_limit_utilization
5. tx_count_2min
6. amount
7. failed_login_count_1h
8. is_new_device
9. total_after_txn
10. is_new_location

These features are meaningful because they align with real fraud-risk signals: merchant risk, unusual amount behavior, new beneficiaries, login behavior, and transaction velocity.

---

## Model Benchmarking Results

FinShield now includes a benchmarking layer that compares supervised ML, neural-network, and anomaly-detection models.

Models benchmarked:

- Logistic Regression
- Random Forest
- Gradient Boosting
- MLP Neural Network
- Isolation Forest
- Autoencoder Anomaly Detector

Best model:

```text
Gradient Boosting
```

Best model metrics:

| Metric | Value |
|---|---:|
| Accuracy | 0.9953 |
| Precision | 0.9882 |
| Recall | 0.9911 |
| F1 Score | 0.9896 |
| ROC AUC | 0.9998 |
| Average Precision / PR-AUC | 0.9993 |
| True Negative | 1159 |
| False Positive | 4 |
| False Negative | 3 |
| True Positive | 334 |
| Latency per Transaction | approximately 0.015 ms |
| Selection Score | 0.9943 |

This benchmark layer makes the project closer to real-world ML practice.

In fraud detection, the best model should not be selected using accuracy alone. False negatives, false positives, recall, PR-AUC, and inference latency matter more.

---

## Anomaly Detection Results

FinShield uses two anomaly-detection approaches:

- Autoencoder Anomaly Detector
- Isolation Forest

The anomaly layer produces:

- autoencoder_anomaly_score
- isolation_forest_anomaly_score
- autoencoder_reconstruction_error
- autoencoder_anomaly_flag
- isolation_forest_anomaly_flag
- anomaly_severity

Anomaly severity distribution:

| Anomaly Severity | Count |
|---|---:|
| LOW | 5019 |
| MEDIUM | 150 |
| HIGH | 831 |

This layer helps the system detect unusual behavior that may not be captured by supervised labels alone.

---

## Anomaly-Aware Final Decision Results

The final decision engine now combines:

- supervised ML fraud score,
- model confidence,
- cybersecurity rule score,
- rule action,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- account takeover signals,
- daily limit signals,
- final reason codes.

Updated final action distribution:

| Final Action | Count |
|---|---:|
| ALLOW | 4278 |
| WARN | 471 |
| BLOCK | 505 |
| LOCK | 746 |

The increase in LOCK decisions is expected because anomaly signals now contribute to escalation when they agree with ML and rule-based risk.

This makes the final engine more capable because it can respond to both known fraud patterns and unknown abnormal behavior.

---

## Anomaly-Aware Decision Sources

The audit system now records where each decision came from.

Decision source categories include:

- NO_RISK_ENGINE_TRIGGERED
- RULE_ENGINE_MONITORED
- ML_RULE_ANOMALY_ENGINE
- ML_AND_RULE_ENGINE
- RULE_ENGINE
- ML_ENGINE
- ML_AND_ANOMALY_ENGINE
- ANOMALY_ENGINE
- RULE_AND_ANOMALY_ENGINE

This is important because the system is no longer a black box. Each decision can be traced to ML, rules, anomaly detection, or a combination of signals.

---

## Audit Log Results

Total audit records generated:

```text
6000
```

Severity distribution:

| Severity | Count |
|---|---:|
| LOW | 4278 |
| MEDIUM | 471 |
| HIGH | 505 |
| CRITICAL | 746 |

Each audit record includes:

- transaction details,
- rule signals,
- ML score,
- model confidence,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- reconstruction error,
- final risk score,
- final action,
- final reason,
- severity,
- decision source,
- ground truth label,
- hardware packet readiness.

This makes every decision reviewable.

---


## Generated Output Files

Main processed files:

```text
data/sample_transactions.csv
data/processed/rule_scored_transactions.csv
data/processed/ml_scored_transactions.csv
data/processed/benchmark_scored_transactions.csv
data/processed/final_decision_transactions.csv
data/processed/audit_log_view.csv
```

Main result files:

```text
results/model_metrics.json
results/feature_importance.csv
results/model_comparison.csv
results/model_comparison.json
results/best_model_summary.json
results/audit_logs.jsonl
results/audit_summary.json
```

---

## Current Status

Completed:

- Synthetic transaction generator
- Cybersecurity rule engine
- Primary ML fraud scoring pipeline
- ML and anomaly model benchmarking
- Deep autoencoder anomaly detection
- Isolation Forest anomaly detection
- Anomaly-aware final decision engine
- Explainable audit logging
- Anomaly traceability in audit records
- Streamlit dashboard
- Audit-ready risk decision trace generation
- One-command pipeline runner

Planned:

- model monitoring and analyst-copilot validation simulation
- Waveform screenshots
- Synthesis/resource utilization report
- Unit tests
- Dashboard screenshots in README

