# Verilog HDL Design Plan

The Verilog HDL layer is the planned hardware-oriented enforcement layer of FinShield HDL.

The Python pipeline already produces compact risk packets containing cybersecurity rule signals, ML fraud scores, anomaly scores, and final decision codes. The Verilog layer will use these packet signals to implement a low-latency kill-switch style enforcement engine.

---

## Purpose

Most fraud detection systems stop at software prediction.

FinShield HDL is designed to go one step further by connecting AI-driven risk decisions to a deterministic hardware-style enforcement layer.

The HDL layer will demonstrate how transaction risk signals can be converted into simple, fast, verifiable logic.

The goal is not to replace the ML model with Verilog. Instead, the goal is to use Verilog for the final enforcement logic after the Python system has generated compact decision signals.

---

## Hardware Enforcement Concept

The Python side computes:

- cybersecurity rule signals,
- ML fraud score,
- model confidence,
- autoencoder anomaly score,
- Isolation Forest anomaly score,
- final risk score,
- final action code.

The Verilog side will consume compact integer versions of those signals and produce hardware-style outputs:

- allow_signal
- warn_signal
- block_signal
- lock_signal
- current_state
- action_code

This creates a clean bridge:

```text
Python Risk Engine
-> Hardware Risk Packet
-> Verilog Checker Modules
-> Kill-Switch FSM
-> Enforcement Output
```

---

## Hardware Input Signals

The HDL engine will use integer-based inputs such as:

- total_after_txn
- daily_limit
- tx_count_2min
- velocity_threshold
- is_new_device
- is_new_location
- failed_login_count_1h
- failed_login_threshold
- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- high_merchant_risk
- failed_login_risk
- rule_risk_score
- ml_fraud_score
- model_confidence
- autoencoder_anomaly_score
- isolation_forest_anomaly_score
- final_risk_score
- admin_reset

Python may use decimal transaction values, but the Verilog layer will use integer representations.

Example:

```text
Python value:   110644.24
Hardware value: 110644
```

For this project, rupee-level integer precision is enough for HDL simulation.

---

## Hardware Output Signals

The HDL engine will output:

- current_state
- action_code
- allow_signal
- warn_signal
- block_signal
- lock_signal

Action encoding:

| Action | Code |
|---|---:|
| ALLOW | 0 |
| WARN | 1 |
| BLOCK | 2 |
| LOCK | 3 |

---

## Planned Verilog Modules

### 1. daily_limit_checker.v

Purpose:

Checks whether the transaction pushes the account beyond the daily limit.

Logic:

```text
daily_limit_breach = total_after_txn > daily_limit
```

Python equivalent:

```text
total_after_txn > daily_limit
```

This is a simple comparator and is suitable for low-latency hardware logic.

---

### 2. velocity_checker.v

Purpose:

Checks whether too many transactions occurred in a short window.

Logic:

```text
velocity_spike = tx_count_2min >= velocity_threshold
```

Python equivalent:

```text
tx_count_2min >= 5
```

This module detects short-term burst activity.

---

### 3. account_takeover_checker.v

Purpose:

Detects account takeover behavior.

Logic:

```text
account_takeover_signal =
    is_new_device
    and is_new_location
    and failed_login_count_1h >= failed_login_threshold
```

Python equivalent:

```text
is_new_device == 1
and is_new_location == 1
and failed_login_count_1h >= 3
```

This signal is treated as high risk because new device, new location, and repeated failed login attempts together are strong account takeover indicators.

---

### 4. risk_threshold_checker.v

Purpose:

Converts ML, anomaly, rule, and final scores into binary hardware risk signals.

Planned signals:

- ml_high_risk
- ml_low_confidence_risk
- rule_high_risk
- autoencoder_high_anomaly
- isolation_high_anomaly
- final_high_risk
- final_critical_risk

Example logic:

```text
ml_high_risk =
    ml_fraud_score >= 75
    and model_confidence >= 70
```

```text
autoencoder_high_anomaly =
    autoencoder_anomaly_score >= 85
```

```text
final_critical_risk =
    final_risk_score >= 90
```

This module converts multi-source risk scores into clean one-bit signals that the FSM can use.

---

### 5. kill_switch_fsm.v

Purpose:

Implements the enforcement state machine.

Planned states:

- NORMAL
- WARNING
- LOCKED

State behavior:

NORMAL:

- Stay in NORMAL when risk is low.
- Move to WARNING when moderate risk appears.
- Move to LOCKED when critical risk appears.

WARNING:

- Return to NORMAL when risk clears.
- Stay in WARNING when risk remains moderate.
- Move to LOCKED when risk escalates.

LOCKED:

- Stay locked until admin_reset is triggered.

The LOCKED state represents a high-risk account/session condition where transaction activity should be stopped until review.

---

### 6. finshield_top.v

Purpose:

Connects all checker modules and the FSM.

This will be the top-level HDL module.

It will combine:

- daily limit checker,
- velocity checker,
- account takeover checker,
- risk threshold checker,
- kill-switch FSM.

---

### 7. tb_finshield_top.v

Purpose:

Provides test vectors for simulation.

The testbench will apply sample risk packets and verify that the HDL engine produces the expected action code.

The testbench will include cases such as:

- normal transaction -> ALLOW
- velocity spike -> WARN
- daily limit breach -> BLOCK
- account takeover -> LOCK
- high ML + high anomaly -> LOCK
- admin reset after LOCKED state

---

## Planned FSM Logic

The FSM will use risk signals generated by the checker modules.

Example decision behavior:

```text
If account_takeover_signal is high:
    LOCK

Else if final_critical_risk is high:
    LOCK

Else if daily_limit_breach is high:
    BLOCK

Else if ml_high_risk and autoencoder_high_anomaly are high:
    LOCK

Else if rule_high_risk or final_high_risk is high:
    BLOCK

Else if velocity_spike or ml_low_confidence_risk is high:
    WARN

Else:
    ALLOW
```

This mirrors the Python decision philosophy while keeping the HDL logic simple and deterministic.

---

## Hardware Packet Mapping

The current Python pipeline generates:

```text
data/processed/hardware_risk_packets.csv
```

This file will be used to create Verilog simulation vectors.

Important packet fields:

- transaction_id
- daily_limit_breach
- velocity_spike
- large_amount_anomaly
- new_beneficiary_risk
- account_takeover_signal
- high_merchant_risk
- failed_login_risk
- rule_risk_score
- ml_fraud_score
- model_confidence
- autoencoder_anomaly_score
- isolation_forest_anomaly_score
- final_risk_score
- final_action_code
- final_action

The final_action_code from Python will be used as the reference output during comparison.

---

## Vivado Simulation Plan

Vivado will be used for:

- adding HDL source files,
- running behavioral simulation,
- viewing waveforms,
- checking FSM transitions,
- verifying action codes,
- running synthesis,
- capturing resource utilization reports.

Expected simulation artifacts:

```text
docs/screenshots/vivado_waveform.png
docs/screenshots/fsm_transition.png
docs/vivado_utilization_summary.md
simulations/verilog_output.txt
```

---

## Python vs Verilog Comparison

After simulation, the project will compare Python and Verilog decisions.

Comparison file:

```text
results/decision_comparison.csv
```

Planned comparison fields:

- transaction_id
- python_final_action_code
- verilog_action_code
- python_final_action
- verilog_action
- match

Example:

| Transaction | Python Action | Verilog Action | Match |
|---|---|---|---|
| TXN_000001 | LOCK | LOCK | YES |
| TXN_000002 | BLOCK | BLOCK | YES |
| TXN_000003 | WARN | WARN | YES |

This will prove that the HDL kill-switch logic mirrors the Python security decision layer.

---

## Why the HDL Layer Matters

The HDL layer makes the project unique.

The Python system handles intelligence:

```text
ML scoring
+ anomaly detection
+ cybersecurity rules
+ audit logs
```

The Verilog system handles deterministic enforcement:

```text
compact risk packet
-> checker logic
-> FSM
-> action code
```

Together, they create the core FinShield HDL idea:

> AI decides risk. HDL enforces the final action quickly and deterministically.

---

## Current Status

Completed on the Python side:

- hardware-ready risk packet generation,
- rule signals,
- ML fraud score,
- anomaly scores,
- final action codes.

Planned on the HDL side:

- checker modules,
- kill-switch FSM,
- top-level module,
- testbench,
- Vivado waveform,
- synthesis report,
- Python vs Verilog comparison.
