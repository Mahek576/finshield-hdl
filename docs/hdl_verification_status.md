# FinShield HDL Verification Status

## Current HDL Status

The FinShield HDL layer has been implemented as source-level Verilog modules, but full Vivado simulation and synthesis proof is pending because Vivado is not currently installed on the development system.

## Implemented Verilog Modules

- `daily_limit_checker.v`
- `velocity_checker.v`
- `risk_threshold_checker.v`
- `account_takeover_checker.v`
- `kill_switch_fsm.v`
- `finshield_top.v`
- `tb_finshield_top.v`

## HDL Design Purpose

The HDL layer represents the hardware-enforcement side of FinShield. It receives risk-related signals from the software/ML layer and converts them into deterministic security actions.

The hardware logic supports:

- Transaction approval
- Step-up authentication
- Kill-switch activation
- Audit event signaling
- Limit violation detection
- Velocity violation detection
- Risk threshold enforcement
- Account takeover pattern detection

## Kill-Switch FSM

```text
NORMAL -> WARNING -> LOCKED -> COOLDOWN -> NORMAL