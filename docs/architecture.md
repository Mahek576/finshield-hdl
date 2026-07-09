# FinShield HDL Architecture

FinShield HDL is a hybrid AI and hardware-oriented fintech security system for transaction risk monitoring and low-latency enforcement.

The project is designed around three layers:

1. Intelligence Layer
2. Security Rule Layer
3. Hardware Enforcement Layer

The current implementation includes the Python-based intelligence, rule, audit, and dashboard layers. The Verilog HDL enforcement layer is designed and will be implemented through Vivado in the next phase.

## System Flow

Transaction Generator
-> Feature Engineering
-> Cybersecurity Rule Engine
-> Primary ML Fraud Model
-> ML and Anomaly Model Benchmarking
-> Hybrid Final Decision Engine
-> Audit Log Engine
-> Streamlit Dashboard
-> Hardware-Ready Risk Packets
-> Verilog Kill-Switch Engine

## Main Components

### 1. Synthetic Transaction Generator

File:

src/data/generate_transactions.py

This module generates synthetic financial transactions with realistic risk patterns.

Generated transaction types include:

- NORMAL
- BENIGN_HIGH_VALUE
- BENIGN_VELOCITY
- HIGH_AMOUNT_RISK
- VELOCITY_SPIKE
- RISKY_BENEFICIARY
- ACCOUNT_TAKEOVER
- SUBTLE_FRAUD
- MIXED_RISK

The generator intentionally adds overlap between normal and fraudulent behavior so that the ML model is not trained on an unrealistically easy dataset.

### 2. Cybersecurity Rule Engine

File:

src/rules/risk_rules.py

The rule engine creates deterministic security signals such as:

- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- high_merchant_risk
- failed_login_risk
- suspicious_hour_activity

It produces:

- rule_risk_score
- rule_action
- reason_codes
- verilog_decision_packets.csv

### 3. ML Fraud Scoring Pipeline

File:

src/ml/train_model.py

The ML pipeline trains a Random Forest classifier using behavioral transaction features.

The model outputs:

- ml_fraud_probability
- ml_fraud_score
- model_confidence
- predicted_fraud

The model is saved to:

models/finshield_fraud_model.joblib

### 4. Model Benchmarking Layer

File:

src/ml/benchmark_models.py

This module benchmarks multiple supervised, neural-network, and anomaly-detection models for fraud scoring.

Models compared:

- Logistic Regression
- Random Forest
- Gradient Boosting
- MLP Neural Network
- Isolation Forest
- Autoencoder Anomaly Detector

The benchmark evaluates each model using:

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

Outputs:

results/model_comparison.csv
results/model_comparison.json
results/best_model_summary.json
data/processed/benchmark_scored_transactions.csv

The benchmark layer makes the intelligence system more realistic because it compares multiple model families before selecting the best-performing model.

### 5. Hybrid Final Decision Engine

File:

src/rules/final_decision_engine.py

This layer combines:

- ML fraud score
- model confidence
- rule risk score
- rule action
- cybersecurity reason codes

It outputs:

- final_risk_score
- final_action
- final_action_code
- final_reason

Final actions are encoded as:

- ALLOW = 0
- WARN = 1
- BLOCK = 2
- LOCK = 3

### 6. Audit Log Engine

File:

src/audit/audit_logger.py

The audit layer generates explainable decision records for every transaction.

Each audit record includes:

- transaction details
- rule signals
- ML scores
- final action
- severity
- decision source
- ground truth label
- hardware packet readiness

Outputs:

results/audit_logs.jsonl
results/audit_summary.json
data/processed/audit_log_view.csv

### 7. Dashboard

File:

src/dashboard/app.py

The Streamlit dashboard provides a visual monitoring interface for:

- final action distribution
- severity distribution
- decision source distribution
- risk type distribution
- ML model performance
- feature importance
- high-risk transactions
- audit log view
- hardware-ready risk packets

### 8. Hardware-Ready Packets

File:

data/processed/hardware_risk_packets.csv

This file contains compact integer risk signals that can be consumed by the Verilog HDL kill-switch engine.

Example signals:

- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- rule_risk_score
- ml_fraud_score
- model_confidence
- final_risk_score
- final_action_code

## Why This Architecture Matters

Most fraud detection projects stop at prediction.

FinShield HDL goes further by creating an enforcement-oriented pipeline:

ML risk scoring
+ deterministic cybersecurity rules
+ audit traceability
+ hardware-ready decision packets
+ planned Verilog kill-switch enforcement

This makes the project stronger for fintech, cybersecurity, AI engineering, and hardware-aware system design roles.
