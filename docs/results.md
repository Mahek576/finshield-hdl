# FinShield HDL Results

This document summarizes the current results of the FinShield HDL pipeline.

## Dataset Summary

The synthetic transaction generator created 6000 financial transactions.

Fraud label distribution:

- Normal transactions: 4652
- Fraud/risky transactions: 1348

Risk type distribution:

- NORMAL: 4141
- HIGH_AMOUNT_RISK: 280
- BENIGN_HIGH_VALUE: 279
- VELOCITY_SPIKE: 244
- SUBTLE_FRAUD: 242
- BENIGN_VELOCITY: 232
- RISKY_BENEFICIARY: 219
- ACCOUNT_TAKEOVER: 204
- MIXED_RISK: 159

The dataset includes realistic overlap between legitimate and suspicious behavior.

Examples:

- A normal user may perform a high-value transaction.
- A normal user may create a temporary velocity spike.
- Some fraud cases may be subtle and not trigger obvious hard rules.

## Cybersecurity Rule Engine Results

Rule action distribution:

- ALLOW: 4557
- WARN: 577
- BLOCK: 547
- LOCK: 319

Average rule risk score by risk type:

- MIXED_RISK: 92.39
- ACCOUNT_TAKEOVER: 83.33
- HIGH_AMOUNT_RISK: 52.61
- RISKY_BENEFICIARY: 42.56
- VELOCITY_SPIKE: 23.14
- BENIGN_VELOCITY: 21.31
- BENIGN_HIGH_VALUE: 9.71
- SUBTLE_FRAUD: 3.35
- NORMAL: 1.26

This shows that the rule engine is strict for clear security violations but does not blindly block every suspicious-looking transaction.

## ML Fraud Model Results

Model used:

Random Forest Classifier

Current metrics:

- Accuracy: 0.9933
- Precision: 0.9739
- Recall: 0.9970
- F1 score: 0.9853
- ROC AUC: 0.9996
- Average precision: 0.9987

Confusion matrix:

- True negative: 1154
- False positive: 9
- False negative: 1
- True positive: 336

The model is strong but not perfectly clean, which is more realistic than an artificial 1.0000 score across every metric.

## Top Feature Importances

The most important model features were:

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

This is meaningful because these features are also strong real-world fraud indicators.

## Hybrid Final Decision Results

Final action distribution:

- ALLOW: 4297
- WARN: 462
- BLOCK: 768
- LOCK: 473

The final decision engine combines ML and rule signals to produce enforcement decisions.

Important examples:

- ACCOUNT_TAKEOVER transactions were locked.
- MIXED_RISK transactions were mostly locked.
- BENIGN_VELOCITY transactions were warned, not blocked.
- BENIGN_HIGH_VALUE transactions were often allowed or warned.
- NORMAL transactions were almost always allowed.

This proves that the system can distinguish between suspicious behavior and confirmed high-risk activity.

## Audit Log Results

Total audit records generated:

6000

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

This is important because the system does not behave like a black box. Every final action is traceable to ML signals, rule signals, monitored signals, or a combination of them.

## Generated Output Files

Main processed files:

- data/sample_transactions.csv
- data/processed/rule_scored_transactions.csv
- data/processed/ml_scored_transactions.csv
- data/processed/final_decision_transactions.csv
- data/processed/hardware_risk_packets.csv
- data/processed/audit_log_view.csv

Main result files:

- results/model_metrics.json
- results/feature_importance.csv
- results/audit_logs.jsonl
- results/audit_summary.json

## Current Status

Completed:

- Synthetic transaction generator
- Cybersecurity rule engine
- ML fraud scoring pipeline
- Hybrid final decision engine
- Audit logging
- Streamlit dashboard
- Hardware-ready risk packet generation

Planned:

- Verilog checker modules
- Verilog kill-switch FSM
- Vivado simulation
- Waveform screenshots
- Synthesis/resource utilization report
- Python vs Verilog decision comparison
