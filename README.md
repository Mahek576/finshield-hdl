# FinShield HDL

FinShield HDL is a hybrid AI and hardware-description-language based fintech security engine for low-latency financial risk enforcement.

The system monitors financial transactions, computes fraud and cybersecurity risk using machine learning and rule-based signals, and sends quantized risk features to a Verilog kill-switch engine. The HDL engine makes fast enforcement decisions such as ALLOW, WARN, BLOCK, or LOCK using a finite-state machine.

## Core Idea

Traditional fraud detection systems usually stop at model prediction. FinShield HDL extends this by adding a hardware-style enforcement layer for deterministic and low-latency decision-making.

## Key Features

- Synthetic financial transaction stream generation
- ML-based fraud risk scoring
- Cybersecurity risk rules
- Account takeover detection
- Velocity risk detection
- Beneficiary risk detection
- Verilog finite-state kill-switch engine
- Python vs Verilog decision comparison
- Audit logs for explainability
- Streamlit dashboard for monitoring

## System Architecture

Transaction Stream
-> Feature Engineering
-> ML Fraud Model
-> Cybersecurity Rule Engine
-> Decision Packet
-> Verilog Kill-Switch FSM
-> Final Action
-> Audit Logs + Dashboard

## Verilog Modules

- daily_limit_checker.v
- velocity_checker.v
- risk_threshold_checker.v
- account_takeover_checker.v
- kill_switch_fsm.v
- finshield_top.v
- tb_finshield_top.v

## FSM States

The kill-switch engine uses three core states:

- NORMAL
- WARNING
- LOCKED

The state machine transitions based on transaction risk, account behavior, transaction velocity, beneficiary risk, and model confidence.

## Project Goal

This project demonstrates the ability to build AI-powered fintech security systems while also thinking about hardware-level low-latency enforcement.
