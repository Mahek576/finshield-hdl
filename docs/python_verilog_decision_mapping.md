# Python to Verilog Decision Mapping

This document explains how the FinShield software decision engine maps to the Verilog HDL enforcement layer.

The purpose of this mapping is to show that the Python, machine learning, anomaly detection, cybersecurity rules, and HDL modules are part of one integrated fintech security pipeline.

FinShield is designed as an AI-powered fintech risk engine where the software layer performs intelligent fraud and anomaly analysis, while the HDL layer provides deterministic hardware-style enforcement through Verilog logic.

---

## 1. High-Level System Flow

```text
Synthetic Transaction
        |
        v
Python Rule Engine + ML Fraud Model + Anomaly Detection
        |
        v
Final Risk Decision + Hardware-Ready Risk Packet
        |
        v
Verilog HDL Enforcement Layer
        |
        v
Allow / Step-Up Authentication / Kill-Switch Block
```

The Python layer performs risk intelligence.

The Verilog layer performs fast, deterministic enforcement.

Together, they form a software-to-hardware security pipeline.

---

## 2. Software Layer Role

The Python layer is responsible for intelligent risk analysis.

It includes:

* Synthetic transaction generation
* Cybersecurity rule engine
* Random Forest fraud detection
* Gradient Boosting model selection
* MLP benchmark
* Isolation Forest anomaly detection
* Autoencoder anomaly detection
* Anomaly-aware final decision logic
* Audit logging and traceability
* Streamlit dashboard monitoring
* Hardware-ready risk packet preparation

The software layer analyzes each transaction and produces structured risk indicators that can be interpreted by the HDL enforcement layer.

---

## 3. HDL Layer Role

The Verilog HDL layer represents deterministic hardware-side enforcement.

It does not train machine learning models or perform complex analytics. Instead, it receives risk-related signals and applies fast hardware logic to decide whether a transaction should be allowed, reviewed, or blocked.

The HDL layer supports:

* Single transaction limit checking
* Daily limit checking
* Transaction velocity checking
* Risk threshold enforcement
* Account takeover pattern detection
* Kill-switch activation
* Step-up authentication signaling
* Audit event signaling

This makes the HDL layer a hardware-enforcement companion to the Python AI risk engine.

---

## 4. Python to HDL Signal Mapping

| Python / Risk Engine Concept        | HDL Signal               | Meaning                                             |
| ----------------------------------- | ------------------------ | --------------------------------------------------- |
| Transaction amount                  | `transaction_amount`     | Current transaction value                           |
| User daily spend before transaction | `daily_total_before`     | Existing daily total before the current transaction |
| Number of recent transactions       | `txn_count_window`       | Transaction velocity indicator                      |
| ML / rule-based risk score          | `risk_score`             | Exported transaction risk score                     |
| ML model confidence                 | `ml_confidence_score`    | Confidence level of the software-side decision      |
| Anomaly model output                | `anomaly_flag`           | Isolation Forest / Autoencoder anomaly signal       |
| New device indicator                | `new_device`             | Possible account takeover signal                    |
| Foreign IP indicator                | `foreign_ip`             | Suspicious login or location signal                 |
| Failed login pattern                | `multiple_failed_logins` | Brute-force or account takeover indicator           |
| Transaction validity                | `txn_valid`              | Marks an active transaction packet                  |
| Manual/security unlock              | `clear_lock`             | Clears the locked state after review                |
| Cooldown completion                 | `cooldown_done`          | Allows the FSM to return to normal operation        |

---

## 5. HDL Module Responsibilities

| Verilog Module               | Responsibility                                            |
| ---------------------------- | --------------------------------------------------------- |
| `daily_limit_checker.v`      | Detects single-transaction and daily-limit violations     |
| `velocity_checker.v`         | Detects excessive transaction frequency                   |
| `risk_threshold_checker.v`   | Converts risk score into warning and block flags          |
| `account_takeover_checker.v` | Detects suspicious account takeover patterns              |
| `kill_switch_fsm.v`          | Controls the NORMAL, WARNING, LOCKED, and COOLDOWN states |
| `finshield_top.v`            | Integrates all HDL enforcement modules                    |
| `tb_finshield_top.v`         | Testbench for behavioral verification                     |

---

## 6. HDL Decision Encoding

The Verilog top module produces a compact final decision code.

| HDL Decision Code | Meaning                                  | Software Equivalent  |
| ----------------- | ---------------------------------------- | -------------------- |
| `2'b00`           | Allow transaction                        | Approved / low risk  |
| `2'b01`           | Require step-up authentication           | Review / medium risk |
| `2'b10`           | Block transaction / activate kill-switch | Blocked / high risk  |

This allows the HDL layer to represent the same final decision categories used by the Python risk engine.

---

## 7. Kill-Switch FSM

The kill-switch FSM is the core hardware-enforcement component.

It follows this state flow:

```text
NORMAL -> WARNING -> LOCKED -> COOLDOWN -> NORMAL
```

| FSM State  | Meaning                                                 |
| ---------- | ------------------------------------------------------- |
| `NORMAL`   | Transactions can proceed normally                       |
| `WARNING`  | Risk is elevated and step-up authentication is required |
| `LOCKED`   | Kill-switch is active and transactions are blocked      |
| `COOLDOWN` | System is recovering after manual/security clearance    |

---

## 8. Decision Logic Alignment

The Python and Verilog layers are expected to align as follows:

| Scenario                            | Python Decision                               | HDL Decision       |
| ----------------------------------- | --------------------------------------------- | ------------------ |
| Safe transaction                    | Allow                                         | `2'b00`            |
| Medium-risk transaction             | Review / step-up authentication               | `2'b01`            |
| High-risk transaction               | Block                                         | `2'b10`            |
| Daily limit violation               | Block                                         | `2'b10`            |
| Single transaction limit violation  | Block                                         | `2'b10`            |
| Excessive transaction velocity      | Review or block depending on risk combination | `2'b01` or `2'b10` |
| Suspicious account takeover pattern | Block                                         | `2'b10`            |
| Anomaly with low ML confidence      | Block                                         | `2'b10`            |
| Mild anomaly or warning threshold   | Review                                        | `2'b01`            |

---

## 9. Implemented HDL Behavior

The HDL top module combines rule-based and risk-based signals into warning and block conditions.

### Warning Conditions

A transaction may require step-up authentication if any of the following are detected:

* Risk score crosses the warning threshold
* Anomaly flag is active
* Velocity violation is detected
* Limit violation is detected
* ML confidence is low
* Account takeover pattern is suspected

### Block Conditions

A transaction may be blocked if any of the following are detected:

* Risk score crosses the block threshold
* Limit violation is detected
* Account takeover pattern is suspected
* Anomaly is detected along with low ML confidence

---

## 10. Hardware-Ready Risk Packet Concept

The software layer can export a simplified risk packet for HDL enforcement.

Example conceptual packet:

```text
transaction_amount
daily_total_before
txn_count_window
risk_score
ml_confidence_score
anomaly_flag
new_device
foreign_ip
multiple_failed_logins
```

The HDL layer consumes these fields as Verilog inputs and produces:

```text
allow_transaction
step_up_auth_required
kill_switch_active
audit_event
final_decision
fsm_state
```

This creates a clean boundary between AI-driven analysis and deterministic hardware enforcement.

---

## 11. Verification Plan

When Vivado is available, the following comparison should be completed:

1. Export sample transaction risk packets from Python.
2. Feed equivalent values into the Verilog testbench.
3. Run behavioral simulation.
4. Observe `final_decision`, `fsm_state`, `allow_transaction`, and `kill_switch_active`.
5. Compare Python final decisions with HDL `final_decision`.
6. Record matched and mismatched cases.
7. Capture waveform screenshots.
8. Add synthesis and utilization reports to the project documentation.

---

## 12. Current Verification Status

| Item                                              | Status   |
| ------------------------------------------------- | -------- |
| Python decision engine                            | Complete |
| Rule engine                                       | Complete |
| ML fraud model                                    | Complete |
| Anomaly detection                                 | Complete |
| Audit logging                                     | Complete |
| Streamlit dashboard                               | Complete |
| HDL enforcement modules                           | Complete |
| HDL top module                                    | Complete |
| HDL testbench                                     | Complete |
| Python-to-Verilog conceptual mapping              | Complete |
| Automated Python vs Verilog simulation comparison | Pending  |
| Vivado behavioral simulation                      | Pending  |
| Waveform screenshot                               | Pending  |
| Vivado synthesis                                  | Pending  |
| Utilization report                                | Pending  |

---

## 13. Honest Project Position

The FinShield software, machine learning, anomaly detection, cybersecurity rules, audit logging, dashboard, and testing layers are complete.

The HDL layer is implemented at source-code level through Verilog modules and a testbench.

Full Vivado-based waveform simulation, synthesis, utilization reporting, and Python-vs-Verilog comparison remain pending because Vivado is not currently installed on the development system.

This keeps the project technically honest while preserving the full AI + HDL fintech security-system vision.

---

## 14. Summary

FinShield combines intelligent software-side risk analysis with deterministic hardware-style enforcement.

The Python layer detects fraud, anomalies, rule violations, and suspicious behavior.

The Verilog HDL layer converts these risk signals into low-latency enforcement actions:

* Allow transaction
* Require step-up authentication
* Activate kill-switch and block transaction

This makes FinShield more than a basic ML fraud detection project. It becomes an AI-powered fintech security system with a hardware-ready enforcement architecture.
