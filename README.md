# FinShield HDL

FinShield HDL is a hybrid AI and hardware-oriented fintech security system for transaction risk monitoring, fraud scoring, cybersecurity rule enforcement, audit traceability, and hardware-ready decision making.

The system simulates financial transactions, detects suspicious behavior using machine learning and deterministic security rules, generates explainable audit logs, and prepares compact risk packets for a planned Verilog HDL kill-switch engine.

## Core Idea

Most fraud detection projects stop at model prediction.

FinShield HDL goes further by building an enforcement-oriented risk pipeline:

```text
Transaction Stream
-> Cybersecurity Rule Engine
-> ML Fraud Model
-> Hybrid Final Decision Engine
-> Audit Logs
-> Streamlit Dashboard
-> Hardware-Ready Risk Packets
-> Planned Verilog Kill-Switch Engine
```

The long-term goal is to connect AI-based fintech security decisions with a deterministic low-latency hardware enforcement layer.

## Key Features

- Synthetic financial transaction generation
- Realistic fraud and risk pattern simulation
- ML-based fraud scoring
- Cybersecurity rule engine
- Account takeover detection
- Velocity risk detection
- New beneficiary risk detection
- Hybrid ML + rule final decision engine
- Explainable audit logs
- Streamlit monitoring dashboard
- Hardware-ready risk packet generation
- Planned Verilog HDL kill-switch FSM
- ML and anomaly model benchmarking
- Logistic Regression, Random Forest, Gradient Boosting, MLP, Isolation Forest, and Autoencoder comparison
- Best-model selection using precision, recall, F1, PR-AUC, false positives, false negatives, and latency

## Risk Types Simulated

The transaction generator creates both normal and suspicious financial activity.

Risk patterns include:

- NORMAL
- BENIGN_HIGH_VALUE
- BENIGN_VELOCITY
- HIGH_AMOUNT_RISK
- VELOCITY_SPIKE
- RISKY_BENEFICIARY
- ACCOUNT_TAKEOVER
- SUBTLE_FRAUD
- MIXED_RISK

The dataset intentionally includes overlap between normal and fraudulent behavior so the model is not trained on an unrealistically easy dataset.

## System Components

### 1. Synthetic Transaction Generator

File:

```text
src/data/generate_transactions.py
```

Generates realistic transaction data with account profiles, transaction amounts, daily limits, velocity patterns, beneficiary age, device changes, location changes, failed login counts, and merchant risk scores.

Output:

```text
data/sample_transactions.csv
```

### 2. Cybersecurity Rule Engine

File:

```text
src/rules/risk_rules.py
```

Detects deterministic security signals such as:

- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- high_merchant_risk
- failed_login_risk
- suspicious_hour_activity

Outputs:

```text
data/processed/rule_scored_transactions.csv
data/processed/verilog_decision_packets.csv
```

### 3. ML Fraud Scoring Pipeline

File:

```text
src/ml/train_model.py
```

Trains a Random Forest fraud classifier using transaction behavior features.

The model outputs:

- ml_fraud_probability
- ml_fraud_score
- model_confidence
- predicted_fraud

Saved model:

```text
models/finshield_fraud_model.joblib
```
Benchmarks multiple supervised, neural, and anomaly-detection models for fintech fraud scoring.

Models compared:

Logistic Regression
Random Forest
Gradient Boosting
MLP Neural Network
Isolation Forest
Autoencoder Anomaly Detector

Evaluation metrics:

accuracy
precision
recall
F1 score
ROC AUC
average precision / PR-AUC
false positives
false negatives
latency per transaction
selection score
Outputs:

results/model_comparison.csv
results/model_comparison.json
results/best_model_summary.json
data/processed/benchmark_scored_transactions.csv

Current best model:

Gradient Boosting

### 4. Hybrid Final Decision Engine

File:

```text
src/rules/final_decision_engine.py
```

Combines ML scores, model confidence, rule risk scores, rule actions, and reason codes.

Final actions:

| Action | Code | Meaning |
|---|---:|---|
| ALLOW | 0 | Transaction is allowed |
| WARN | 1 | Transaction is suspicious and should be monitored |
| BLOCK | 2 | Transaction should be blocked |
| LOCK | 3 | Account/session should be locked until review |

Outputs:

```text
data/processed/final_decision_transactions.csv
data/processed/hardware_risk_packets.csv
```

### 5. Audit Log Engine

File:

```text
src/audit/audit_logger.py
```

Generates explainable audit records for every transaction decision.

Each audit record includes:

- transaction details
- rule signals
- ML score
- model confidence
- final risk score
- final action
- severity
- decision source
- ground truth label
- hardware packet readiness

Outputs:

```text
results/audit_logs.jsonl
results/audit_summary.json
data/processed/audit_log_view.csv
```

### 6. Streamlit Dashboard

File:

```text
src/dashboard/app.py
```

The dashboard shows:

- transaction counts
- ALLOW / WARN / BLOCK / LOCK distribution
- severity distribution
- decision source distribution
- risk type distribution
- ML model performance
- feature importance
- high-risk transaction review
- audit log view
- hardware-ready risk packets

## Project Structure

```text
finshield-hdl/
+-- data/
�   +-- raw/
�   +-- processed/
�   +-- sample_transactions.csv
+-- docs/
�   +-- architecture.md
�   +-- results.md
�   +-- verilog_design.md
+-- hdl/
�   +-- daily_limit_checker.v
�   +-- velocity_checker.v
�   +-- risk_threshold_checker.v
�   +-- account_takeover_checker.v
�   +-- kill_switch_fsm.v
�   +-- finshield_top.v
�   +-- tb_finshield_top.v
+-- models/
�   +-- finshield_fraud_model.joblib
+-- results/
�   +-- model_metrics.json
�   +-- feature_importance.csv
�   +-- audit_logs.jsonl
�   +-- audit_summary.json
+-- simulations/
+-- src/
�   +-- audit/
�   +-- comparison/
�   +-- dashboard/
�   +-- data/
�   +-- features/
�   +-- ml/
�   +-- rules/
+-- run_pipeline.py
+-- README.md
+-- requirements.txt
+-- .gitignore
```

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

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Run the Full Pipeline

Recommended one-command pipeline:

```powershell
python run_pipeline.py
```

This runs:

1. Synthetic transaction generation
2. Cybersecurity rule scoring
3. ML fraud model training
4. Hybrid final decision generation
5. Audit log generation

You can also run each step manually:

```powershell
python src\data\generate_transactions.py
python src\rules\risk_rules.py
python src\ml\train_model.py
python src\rules\final_decision_engine.py
python src\audit\audit_logger.py
```

## Run the Dashboard

```powershell
streamlit run src\dashboard\app.py
```

Open:

```text
http://localhost:8501
```

## Current Results

### Dataset

Total transactions:

- 6000

Fraud label distribution:

- Normal transactions: 4652
- Fraud/risky transactions: 1348

### Rule Engine

Rule action distribution:

- ALLOW: 4557
- WARN: 577
- BLOCK: 547
- LOCK: 319

### ML Fraud Model

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

This benchmark layer makes the system closer to real-world ML practice because the final model is selected using fraud-relevant metrics, not accuracy alone.
### Hybrid Final Decision Engine

Final action distribution:

- ALLOW: 4297
- WARN: 462
- BLOCK: 768
- LOCK: 473

### Audit Logs

Total audit records:

- 6000

Severity distribution:

- LOW: 4297
- MEDIUM: 462
- HIGH: 768
- CRITICAL: 473

Decision source distribution:

- NO_RISK_ENGINE_TRIGGERED: 3232
- RULE_ENGINE_MONITORED: 1079
- ML_AND_RULE_ENGINE: 1118
- RULE_ENGINE: 325
- ML_ENGINE: 246

## Verilog HDL Plan

The Verilog HDL layer will act as the low-latency hardware-oriented enforcement engine.

Planned modules:

- daily_limit_checker.v
- velocity_checker.v
- risk_threshold_checker.v
- account_takeover_checker.v
- kill_switch_fsm.v
- finshield_top.v
- tb_finshield_top.v

Planned FSM states:

- NORMAL
- WARNING
- LOCKED

Planned FSM behavior:

```text
NORMAL  -> WARNING  when moderate risk appears
NORMAL  -> LOCKED   when critical risk appears
WARNING -> NORMAL   when risk clears
WARNING -> LOCKED   when risk escalates
LOCKED  -> NORMAL   only after admin reset
```

Vivado will be used later for:

- behavioral simulation
- waveform viewing
- FSM verification
- synthesis
- resource utilization report

## Future Work

- Complete Verilog checker modules
- Implement kill-switch FSM
- Build Verilog testbench
- Generate HDL simulation vectors from hardware_risk_packets.csv
- Compare Python final_action_code with Verilog action_code
- Add Vivado waveform screenshots
- Add synthesis and utilization report

## Project Status

Completed:

- Synthetic transaction generator
- Cybersecurity rule engine
- ML fraud scoring pipeline
- Hybrid final decision engine
- Audit logging
- Streamlit dashboard
- Architecture documentation
- Results documentation
- Hardware-ready risk packet generation
- One-command pipeline runner
- ML and anomaly model benchmarking
- Best-model selection based on fraud metrics and inference latency

Planned:

- Vivado Verilog implementation
- Python vs Verilog comparison
- Waveform screenshots
- Synthesis report

## Resume Description

FinShield HDL is an AI-powered fintech security engine that combines ML fraud scoring, cybersecurity rules, audit traceability, and hardware-ready risk packets for a planned Verilog HDL kill-switch enforcement layer.

## Short Project Summary

Built a hybrid AI + HDL-oriented fintech risk engine that detects suspicious financial transactions using ML and cybersecurity rules, generates explainable audit logs, and prepares compact risk packets for low-latency Verilog-based kill-switch enforcement.
