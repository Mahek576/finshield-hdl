# Verilog HDL Design Plan

The Verilog HDL layer is the hardware-oriented enforcement layer of FinShield HDL.

The goal is to convert selected risk signals into low-latency hardware decisions.

The Verilog implementation will be completed in Vivado.

## Purpose

The Python system generates fraud scores, rule signals, and final risk packets.

The Verilog layer will consume compact integer signals and enforce decisions through a finite-state machine.

This makes the project different from a normal fraud detection project.

Instead of stopping at prediction, FinShield HDL adds a hardware-style kill-switch engine.

## Hardware Input Signals

The HDL engine will use signals such as:

- total_after_txn
- daily_limit
- tx_count_2min
- velocity_threshold
- is_new_device
- is_new_location
- failed_login_count_1h
- failed_login_threshold
- ml_fraud_score
- model_confidence
- rule_risk_score
- final_risk_score

All values will be integer-based.

Python may use decimal transaction values, but the Verilog layer will use integer representations for hardware compatibility.

Example:

Python value:

110644.24

Hardware value:

110644

## Planned Verilog Modules

### 1. daily_limit_checker.v

Purpose:

Checks whether the transaction causes the account to exceed the daily limit.

Logic:

daily_limit_breach = total_after_txn > daily_limit

Python equivalent:

daily_limit_breach = total_after_txn > daily_limit

### 2. velocity_checker.v

Purpose:

Checks whether too many transactions happened in a short time window.

Logic:

velocity_spike = tx_count_2min >= velocity_threshold

Python equivalent:

velocity_spike = tx_count_2min >= 5

### 3. risk_threshold_checker.v

Purpose:

Converts ML and rule scores into binary hardware risk signals.

Signals:

- ml_high_risk
- ml_low_confidence_risk
- rule_high_risk
- final_high_risk
- final_critical_risk

Example logic:

ml_high_risk = ml_fraud_score >= 75 and model_confidence >= 70

final_critical_risk = final_risk_score >= 90

### 4. account_takeover_checker.v

Purpose:

Detects account takeover patterns.

Logic:

account_takeover_signal =
new_device and new_location and failed_login_count_1h >= threshold

Python equivalent:

account_takeover_signal =
is_new_device == 1 and is_new_location == 1 and failed_login_count_1h >= 3

### 5. kill_switch_fsm.v

Purpose:

Implements the hardware enforcement state machine.

Planned states:

- NORMAL
- WARNING
- LOCKED

State behavior:

NORMAL:
- Stay normal if risk is low.
- Move to WARNING if moderate risk appears.
- Move to LOCKED if critical risk appears.

WARNING:
- Return to NORMAL if risk clears.
- Stay in WARNING if risk remains moderate.
- Move to LOCKED if critical risk appears.

LOCKED:
- Stay locked until admin_reset is triggered.

### 6. finshield_top.v

Purpose:

Connects all checker modules and the FSM.

This will be the top-level HDL module.

### 7. tb_finshield_top.v

Purpose:

Verilog testbench for simulation.

The testbench will apply sample risk packets and verify that the HDL engine outputs the correct action.

## Planned HDL Output Signals

The HDL engine will output:

- current_state
- action_code
- allow_signal
- warn_signal
- block_signal
- lock_signal

Action encoding:

- ALLOW = 0
- WARN = 1
- BLOCK = 2
- LOCK = 3

## Vivado Plan

Vivado will be used for:

- Adding HDL source files
- Running behavioral simulation
- Viewing waveforms
- Checking FSM transitions
- Running synthesis
- Capturing utilization reports

## Python vs Verilog Comparison

After the Verilog simulation is working, the project will compare:

- Python final_action_code
- Verilog action_code
- Python final_risk_score
- HDL state transition
- Match or mismatch

This will prove that the HDL enforcement engine mirrors the Python security logic.

## Current Status

The Python system already generates:

data/processed/hardware_risk_packets.csv

This file will be used as the basis for Verilog simulation test vectors.

The Vivado implementation is planned for the next project phase.
