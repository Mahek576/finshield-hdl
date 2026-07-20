# FinShield Architecture

FinShield is an AI-powered fintech security architecture designed for transaction risk monitoring, fraud scoring, anomaly detection, cybersecurity rule enforcement, audit traceability, and explainable and audit-ready risk decisioning.

The project is built around one central idea:

> A fintech security system should not stop at fraud prediction. It should produce explainable, enforceable, and low-latency security decisions.


---

## Architecture Goal

The goal of FinShield is to simulate how a real fintech risk system could make fast security decisions for financial transactions.

A typical fraud detection project ends here:

```text
Dataset -> ML Model -> Accuracy
```

FinShield goes further:

```text
Transaction Stream
-> Feature Engineering
-> Cybersecurity Rule Engine
-> Primary ML Fraud Model
-> ML and Anomaly Model Benchmarking
-> Autoencoder + Isolation Forest Anomaly Signals
-> Hybrid ML + Rule + Anomaly Decision Engine
-> Audit Logs
-> Streamlit Dashboard
-> Audit-Ready Risk Traces
-> Planned LLM/RAG investigation layer Risk Escalation Workflow
```

This makes the project closer to a real security platform than a standalone notebook.

---

## Core Layers

FinShield is organized into five major layers:

1. Data and transaction simulation layer
2. Intelligence and anomaly detection layer
3. Cybersecurity rule layer
4. Decision, audit, and dashboard layer
5. AI risk intelligence and analyst investigation layer

---

## 1. Transaction Simulation Layer

### File

```text
src/data/generate_transactions.py
```

This layer generates synthetic financial transactions with realistic risk signals.

The generated transaction types include:

- NORMAL
- BENIGN_HIGH_VALUE
- BENIGN_VELOCITY
- HIGH_AMOUNT_RISK
- VELOCITY_SPIKE
- RISKY_BENEFICIARY
- ACCOUNT_TAKEOVER
- SUBTLE_FRAUD
- MIXED_RISK

The dataset intentionally contains overlap between legitimate and suspicious behavior.

For example:

- a genuine customer may perform a high-value transfer,
- a normal account may temporarily show high transaction velocity,
- some fraud cases may appear subtle and avoid obvious hard-rule triggers.

This makes the dataset more realistic than a perfectly separated synthetic fraud dataset.

### Output

```text
data/sample_transactions.csv
```

---

## 2. Cybersecurity Rule Engine

### File

```text
src/rules/risk_rules.py
```

The rule engine applies deterministic cybersecurity and transaction-risk checks.

It generates signals such as:

- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- high_merchant_risk
- failed_login_risk
- suspicious_hour_activity

The rule engine produces:

- rule_risk_score
- rule_action
- reason_codes

This layer is important because real fintech systems cannot rely only on model probabilities. Certain security events, such as account takeover signals or daily-limit breaches, require deterministic enforcement.

### Outputs

```text
data/processed/rule_scored_transactions.csv
```

---

## 3. Primary ML Fraud Model

### File

```text
src/ml/train_model.py
```

The primary fraud model is a supervised Random Forest classifier trained on transaction behavior features.

It produces:

- ml_fraud_probability
- ml_fraud_score
- model_confidence
- predicted_fraud

The model is trained on behavioral signals such as amount patterns, transaction velocity, beneficiary age, failed login count, merchant risk score, and account-level usage features.

### Outputs

```text
models/finshield_fraud_model.joblib
data/processed/ml_scored_transactions.csv
results/model_metrics.json
results/feature_importance.csv
```

---

## 4. ML and Anomaly Model Benchmarking

### File

```text
src/ml/benchmark_models.py
```

The benchmarking layer compares multiple supervised, neural-network, and anomaly-detection models.

Models compared:

- Logistic Regression
- Random Forest
- Gradient Boosting
- MLP Neural Network
- Isolation Forest
- Autoencoder Anomaly Detector

The benchmark evaluates each model using fraud-relevant metrics:

- accuracy
- precision
- recall
- F1 score
- ROC AUC
- average precision / PR-AUC
- false positives
- false negatives
- latency per transaction
- selection score

The best model is not selected using accuracy alone. It is selected using metrics that matter in fintech fraud systems: catching fraud, reducing false alerts, and keeping inference latency low.

### Current Best Model

```text
Gradient Boosting
```

### Outputs

```text
results/model_comparison.csv
results/model_comparison.json
results/best_model_summary.json
data/processed/benchmark_scored_transactions.csv
```

---

## 5. Anomaly Detection Layer

The anomaly detection layer adds unsupervised and deep-learning based risk signals to the system.

Models used:

- Autoencoder Anomaly Detector
- Isolation Forest

The autoencoder learns normal transaction behavior and flags transactions with high reconstruction error.

The Isolation Forest identifies unusual transaction patterns without depending only on fraud labels.

Generated anomaly signals:

- autoencoder_anomaly_score
- isolation_forest_anomaly_score
- autoencoder_reconstruction_error
- autoencoder_anomaly_flag
- isolation_forest_anomaly_flag
- anomaly_severity

This layer helps the system detect unknown or subtle abnormal behavior that may not match previously labeled fraud patterns.

---

## 6. Hybrid ML + Rule + Anomaly Decision Engine

### File

```text
src/rules/final_decision_engine.py
```

This is the main enforcement logic layer.

It combines:

- supervised ML fraud score,
- model confidence,
- cybersecurity rule score,
- rule action,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- reconstruction error,
- account takeover signals,
- daily limit signals,
- velocity and beneficiary risk,
- final reason codes.

The final decision engine produces:

- final_risk_score
- final_action
- final_action_code
- final_reason

Final action encoding:

| Action | Code | Meaning |
|---|---:|---|
| ALLOW | 0 | Transaction is allowed |
| WARN | 1 | Transaction is suspicious and should be monitored |
| BLOCK | 2 | Transaction should be blocked |
| LOCK | 3 | Account/session should be locked until review |

### Outputs

```text
data/processed/final_decision_transactions.csv
```

---

## 7. Audit Log Engine

### File

```text
src/audit/audit_logger.py
```

The audit layer converts every transaction decision into an explainable audit record.

Each audit record includes:

- transaction details,
- cybersecurity rule signals,
- ML fraud score,
- model confidence,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- reconstruction error,
- final risk score,
- final action,
- final reason,
- severity,
- decision source,
- anomaly severity,
- ground truth label,
- hardware packet readiness.

This makes the system reviewable and explainable.

Instead of only saying:

```text
Transaction was blocked.
```

the system can explain:

```text
Transaction was locked because the rule engine detected account takeover behavior, the ML model predicted fraud, and both anomaly detectors marked the transaction as abnormal.
```

### Outputs

```text
results/audit_logs.jsonl
results/audit_summary.json
data/processed/audit_log_view.csv
```

---

## 8. Streamlit Dashboard

### File

```text
src/dashboard/app.py
```

The dashboard provides a monitoring interface for:

- transaction counts,
- ALLOW / WARN / BLOCK / LOCK distribution,
- severity distribution,
- decision source distribution,
- risk type distribution,
- ML fraud score,
- rule risk score,
- final risk score,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- anomaly severity distribution,
- model benchmarking results,
- feature importance,
- high-risk transaction review,
- audit log inspection,
- audit-ready decision trace preview.

This gives the project a visual and operational layer instead of leaving the system as command-line output only.

---


## Why This Architecture Is Strong

FinShield is not just a fraud classifier.

It is an end-to-end fintech security architecture that combines:

```text
Supervised ML fraud scoring
+ anomaly detection
+ deterministic cybersecurity rules
+ explainable audit logs
+ dashboard monitoring
+ audit-ready risk decision traces
```

This architecture demonstrates system-level thinking across AI, fintech security, cybersecurity rules, explainability, and hardware-aware decision design.

