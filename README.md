# FinShield HDL

**FinShield HDL** is an AI-powered fintech security system that combines fraud detection, cybersecurity rules, anomaly detection, audit traceability, dashboard monitoring, and hardware-ready decision packets for future Verilog HDL-based low-latency enforcement.

The project is designed to answer one core question:

> Can an AI-driven fintech risk engine make fast, explainable, and hardware-ready security decisions for suspicious financial transactions?

Most fraud detection projects stop at model prediction. FinShield HDL goes further by building an enforcement-oriented pipeline that produces final security actions such as `ALLOW`, `WARN`, `BLOCK`, and `LOCK`.

---

## Why This Project Matters

Financial fraud systems cannot rely on one model alone.

A real-world risk engine must combine:

- supervised fraud prediction,
- deterministic security rules,
- anomaly detection for unknown patterns,
- explainable audit logs,
- operational dashboards,
- and low-latency enforcement logic.

FinShield HDL is built around that idea.

It combines **machine learning**, **deep anomaly detection**, **cybersecurity rule enforcement**, and **hardware-aware decision packets** into one end-to-end fintech security pipeline.

---

## System Overview

```text
Transaction Stream
-> Feature Engineering
-> Cybersecurity Rule Engine
-> Primary ML Fraud Model
-> ML + Anomaly Model Benchmarking
-> Autoencoder + Isolation Forest Anomaly Signals
-> Hybrid ML + Rule + Anomaly Decision Engine
-> Audit Logs
-> Streamlit Dashboard
-> Hardware-Ready Risk Packets
-> Planned Verilog HDL Kill-Switch FSM
```

The current implementation focuses on the Python, ML, anomaly detection, audit, dashboard, and hardware-packet layers.

The Verilog/Vivado layer is planned as the next phase.

---

## Key Capabilities

- Synthetic fintech transaction generation
- Realistic fraud and risk-pattern simulation
- Cybersecurity rule engine
- Account takeover detection
- Velocity risk detection
- New beneficiary risk detection
- Daily limit breach detection
- Supervised ML fraud scoring
- ML and anomaly model benchmarking
- Logistic Regression, Random Forest, Gradient Boosting, MLP, Isolation Forest, and Autoencoder comparison
- Best-model selection using fraud-relevant metrics and latency
- Deep autoencoder anomaly detection
- Isolation Forest anomaly detection
- Hybrid ML + rule + anomaly final decision engine
- Explainable audit logs
- Anomaly traceability in audit records
- Streamlit dashboard for monitoring
- Hardware-ready risk packet generation
- Planned Verilog HDL kill-switch FSM

---

## Risk Types Simulated

The transaction generator creates both normal and suspicious financial behavior.

Simulated transaction categories include:

- `NORMAL`
- `BENIGN_HIGH_VALUE`
- `BENIGN_VELOCITY`
- `HIGH_AMOUNT_RISK`
- `VELOCITY_SPIKE`
- `RISKY_BENEFICIARY`
- `ACCOUNT_TAKEOVER`
- `SUBTLE_FRAUD`
- `MIXED_RISK`

The dataset intentionally includes overlap between legitimate and suspicious behavior. For example, a genuine customer may perform a high-value transfer, and some fraud cases may appear subtle. This prevents the model from learning an unrealistically easy classification problem.

---

## System Components

### 1. Synthetic Transaction Generator

**File**

```text
src/data/generate_transactions.py
```

Generates synthetic financial transactions with realistic behavioral signals:

- transaction amount,
- daily transaction limit,
- account age,
- average transaction amount,
- beneficiary age,
- device change,
- location change,
- failed login count,
- transaction velocity,
- merchant risk score.

**Output**

```text
data/sample_transactions.csv
```

---

### 2. Cybersecurity Rule Engine

**File**

```text
src/rules/risk_rules.py
```

Applies deterministic risk rules that mirror real fintech security checks.

Signals generated include:

- `daily_limit_breach`
- `velocity_spike`
- `large_amount_anomaly`
- `new_beneficiary_risk`
- `account_takeover_signal`
- `high_merchant_risk`
- `failed_login_risk`
- `suspicious_hour_activity`

The rule engine outputs:

- `rule_risk_score`
- `rule_action`
- `reason_codes`
- Verilog-oriented decision packets

**Outputs**

```text
data/processed/rule_scored_transactions.csv
data/processed/verilog_decision_packets.csv
```

---

### 3. Primary ML Fraud Scoring Pipeline

**File**

```text
src/ml/train_model.py
```

Trains a Random Forest classifier for supervised fraud scoring.

The model produces:

- `ml_fraud_probability`
- `ml_fraud_score`
- `model_confidence`
- `predicted_fraud`

**Saved model**

```text
models/finshield_fraud_model.joblib
```

**Outputs**

```text
data/processed/ml_scored_transactions.csv
results/model_metrics.json
results/feature_importance.csv
```

---

### 4. ML and Anomaly Model Benchmarking

**File**

```text
src/ml/benchmark_models.py
```

Benchmarks multiple supervised, neural-network, and anomaly-detection models.

Models compared:

- Logistic Regression
- Random Forest
- Gradient Boosting
- MLP Neural Network
- Isolation Forest
- Autoencoder Anomaly Detector

Evaluation metrics:

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

The best model is selected using fraud-relevant metrics, not accuracy alone.

**Current best model**

```text
Gradient Boosting
```

**Outputs**

```text
results/model_comparison.csv
results/model_comparison.json
results/best_model_summary.json
data/processed/benchmark_scored_transactions.csv
```

---

### 5. Anomaly Detection Layer

The anomaly detection layer adds unsupervised and deep-learning based risk signals.

Models used:

- Autoencoder Anomaly Detector
- Isolation Forest

The autoencoder learns normal transaction behavior and flags transactions with high reconstruction error.

The Isolation Forest detects unusual transaction patterns without relying only on fraud labels.

Generated anomaly signals:

- `autoencoder_anomaly_score`
- `isolation_forest_anomaly_score`
- `autoencoder_reconstruction_error`
- `autoencoder_anomaly_flag`
- `isolation_forest_anomaly_flag`
- `anomaly_severity`

These signals are integrated into the final decision engine and audit logs.

This allows FinShield HDL to detect both known fraud patterns and unknown abnormal behavior.

---

### 6. Hybrid Final Decision Engine

**File**

```text
src/rules/final_decision_engine.py
```

Combines:

- ML fraud score,
- model confidence,
- cybersecurity rule score,
- rule action,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- anomaly reconstruction error,
- account takeover signals,
- final reason codes.

The engine produces the final transaction decision.

| Action | Code | Meaning |
|---|---:|---|
| ALLOW | 0 | Transaction is allowed |
| WARN | 1 | Transaction is suspicious and should be monitored |
| BLOCK | 2 | Transaction should be blocked |
| LOCK | 3 | Account/session should be locked until review |

**Outputs**

```text
data/processed/final_decision_transactions.csv
data/processed/hardware_risk_packets.csv
```

---

### 7. Audit Log Engine

**File**

```text
src/audit/audit_logger.py
```

Generates explainable audit records for every transaction decision.

Each audit record includes:

- transaction details,
- rule signals,
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
- ground truth label,
- hardware packet readiness.

Audit logs make the system explainable and reviewable.

**Outputs**

```text
results/audit_logs.jsonl
results/audit_summary.json
data/processed/audit_log_view.csv
```

---

### 8. Streamlit Dashboard

**File**

```text
src/dashboard/app.py
```

The dashboard provides a monitoring interface for:

- transaction counts,
- final action distribution,
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
- hardware-ready risk packet preview.

---

## Project Structure

```text
finshield-hdl/
|
+-- data/
|   +-- raw/
|   +-- processed/
|   +-- sample_transactions.csv
|
+-- docs/
|   +-- architecture.md
|   +-- results.md
|   +-- verilog_design.md
|
+-- hdl/
|   +-- daily_limit_checker.v
|   +-- velocity_checker.v
|   +-- risk_threshold_checker.v
|   +-- account_takeover_checker.v
|   +-- kill_switch_fsm.v
|   +-- finshield_top.v
|   +-- tb_finshield_top.v
|
+-- models/
|   +-- finshield_fraud_model.joblib
|
+-- results/
|   +-- model_metrics.json
|   +-- feature_importance.csv
|   +-- model_comparison.csv
|   +-- model_comparison.json
|   +-- best_model_summary.json
|   +-- audit_logs.jsonl
|   +-- audit_summary.json
|
+-- simulations/
|
+-- src/
|   +-- audit/
|   +-- comparison/
|   +-- dashboard/
|   +-- data/
|   +-- features/
|   +-- ml/
|   +-- rules/
|
+-- run_pipeline.py
+-- README.md
+-- requirements.txt
+-- .gitignore
```

---

## Tech Stack

- Python
- pandas
- NumPy
- scikit-learn
- Streamlit
- joblib
- Verilog HDL
- Vivado planned for HDL simulation and synthesis
- Git/GitHub

---

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## Run the Full Pipeline

Recommended one-command pipeline:

```powershell
python run_pipeline.py
```

This runs:

1. Synthetic transaction generation
2. Cybersecurity rule scoring
3. Primary ML fraud model training
4. ML and anomaly model benchmarking
5. Hybrid ML + rule + anomaly final decision generation
6. Audit log generation

You can also run each step manually:

```powershell
python src\data\generate_transactions.py
python src\rules\risk_rules.py
python src\ml\train_model.py
python src\ml\benchmark_models.py
python src\rules\final_decision_engine.py
python src\audit\audit_logger.py
```

---

## Run the Dashboard

```powershell
streamlit run src\dashboard\app.py
```

Open:

```text
http://localhost:8501
```

---

## Current Results

### Dataset

Total transactions:

- 6000

Fraud label distribution:

- Normal transactions: 4652
- Fraud/risky transactions: 1348

---

### Cybersecurity Rule Engine

Rule action distribution:

- ALLOW: 4557
- WARN: 577
- BLOCK: 547
- LOCK: 319

---

### Primary ML Fraud Model

Model:

- Random Forest Classifier

Metrics:

- Accuracy: 0.9933
- Precision: 0.9739
- Recall: 0.9970
- F1 score: 0.9853
- ROC AUC: 0.9996
- Average precision / PR-AUC: 0.9987

Confusion matrix:

- True negative: 1154
- False positive: 9
- False negative: 1
- True positive: 336

---

### Model Benchmarking Results

Models compared:

- Logistic Regression
- Random Forest
- Gradient Boosting
- MLP Neural Network
- Isolation Forest
- Autoencoder Anomaly Detector

Best model:

- Gradient Boosting

Best model metrics:

- Accuracy: 0.9953
- Precision: 0.9882
- Recall: 0.9911
- F1 score: 0.9896
- ROC AUC: 0.9998
- Average precision / PR-AUC: 0.9993
- False positives: 4
- False negatives: 3
- Latency per transaction: approximately 0.015 ms
- Selection score: 0.9943

---

### Anomaly-Aware Final Decision Results

The final decision engine now combines supervised fraud scoring, deterministic rules, and anomaly-detection signals.

Updated final action distribution:

- ALLOW: 4278
- WARN: 471
- BLOCK: 505
- LOCK: 746

Anomaly severity distribution:

- LOW: 5019
- MEDIUM: 150
- HIGH: 831

Anomaly-aware decision sources include:

- `ML_RULE_ANOMALY_ENGINE`
- `ML_AND_ANOMALY_ENGINE`
- `RULE_AND_ANOMALY_ENGINE`
- `ANOMALY_ENGINE`

This shows that anomaly detection is actively contributing to final security decisions instead of being used only for benchmarking.

---

### Audit Logs

Total audit records:

- 6000

Severity distribution:

- LOW: 4278
- MEDIUM: 471
- HIGH: 505
- CRITICAL: 746

Decision source distribution includes:

- `NO_RISK_ENGINE_TRIGGERED`
- `RULE_ENGINE_MONITORED`
- `ML_RULE_ANOMALY_ENGINE`
- `ML_AND_RULE_ENGINE`
- `RULE_ENGINE`
- `ML_ENGINE`
- `ML_AND_ANOMALY_ENGINE`
- `ANOMALY_ENGINE`
- `RULE_AND_ANOMALY_ENGINE`

---

## Hardware-Ready Risk Packets

FinShield HDL generates compact decision packets for future HDL simulation.

These packets include:

- rule signals,
- ML fraud score,
- model confidence,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- final risk score,
- final action code.

Output:

```text
data/processed/hardware_risk_packets.csv
```

These packets are designed to be consumed by a Verilog kill-switch FSM in the next phase.

---

## Verilog HDL Plan

The Verilog HDL layer will act as the low-latency hardware-oriented enforcement engine.

Planned modules:

- `daily_limit_checker.v`
- `velocity_checker.v`
- `risk_threshold_checker.v`
- `account_takeover_checker.v`
- `kill_switch_fsm.v`
- `finshield_top.v`
- `tb_finshield_top.v`

Planned FSM states:

- `NORMAL`
- `WARNING`
- `LOCKED`

Planned FSM behavior:

```text
NORMAL  -> WARNING  when moderate risk appears
NORMAL  -> LOCKED   when critical risk appears
WARNING -> NORMAL   when risk clears
WARNING -> LOCKED   when risk escalates
LOCKED  -> NORMAL   only after admin reset
```

Vivado will be used later for:

- behavioral simulation,
- waveform viewing,
- FSM verification,
- synthesis,
- resource utilization report.

---

## Future Work

- Complete Verilog checker modules
- Implement kill-switch FSM
- Build Verilog testbench
- Generate HDL simulation vectors from `hardware_risk_packets.csv`
- Compare Python `final_action_code` with Verilog `action_code`
- Add Vivado waveform screenshots
- Add synthesis and utilization report
- Add dashboard screenshots to README
- Add unit tests for the rule engine, final decision engine, and audit logger

---

## Project Status

Completed:

- Synthetic transaction generator
- Cybersecurity rule engine
- Primary ML fraud scoring pipeline
- ML and anomaly model benchmarking
- Deep autoencoder anomaly detection
- Isolation Forest anomaly detection
- Anomaly-aware final decision engine
- Explainable audit logging
- Anomaly traceability in audit logs
- Streamlit dashboard
- Hardware-ready risk packet generation
- Architecture documentation
- Results documentation
- One-command pipeline runner

Planned:

- Vivado Verilog implementation
- Python vs Verilog comparison
- Waveform screenshots
- Synthesis report
- Dashboard screenshots
- Unit tests

---

## Resume Description

Built **FinShield HDL**, an AI-powered fintech security engine that combines supervised fraud detection, anomaly detection, cybersecurity rules, audit traceability, dashboard monitoring, and hardware-ready risk packets for a planned Verilog HDL kill-switch enforcement layer.

---

## Short Project Summary

FinShield HDL is a hybrid AI + HDL-oriented fintech risk engine that detects suspicious transactions using ML, deep anomaly detection, and cybersecurity rules, generates explainable audit logs, and prepares compact decision packets for low-latency Verilog-based enforcement.