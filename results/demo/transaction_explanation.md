## FinShield Analyst Explanation

Analyst question: Why was this transaction blocked?

### Decision Summary

- Transaction ID: `TXN-DEMO-001`
- User ID: `USER-DEMO-001`
- Final Decision: `BLOCK`
- Fraud Probability: `0.910`
- Adjusted Risk Score: `0.940`
- Model Confidence: `0.820`
- Anomaly Flag: `True`
- Triggered Rules: velocity_violation, foreign_ip, new_device, account_takeover_pattern

### Explanation

FinShield blocked this transaction because the combined evidence indicates high operational fraud risk.

### Evidence

- Fraud probability is high at 0.910.
- Adjusted risk score is block-level at 0.940.
- Anomaly detection flagged unusual transaction behavior.
- Model confidence is acceptable at 0.820.
- Transaction velocity is higher than expected.
- Transaction context includes a foreign IP or unusual location signal.
- Transaction was initiated from a new or unfamiliar device.
- Combined signals suggest possible account takeover behavior.

### Retrieved Policy Context

Source: docs\risk_policy.md
Relevance score: 0.257
cannot approve, block, reverse, or override transaction decisions.

## ALLOW Policy

A transaction may be allowed when:

- Fraud probability is low
- Rule severity is low or absent
- No major anomaly is detected
- Model confidence is acceptable
- Cost-sensitive risk score is below the review threshold

Allowed transactions are still retained in the audit trail.

## REVIEW Policy

A transaction should be reviewed when:

- Fraud probability is elevated but not severe
- Anomaly detection flags unusual behavior
- Transaction velocity is suspicious
- Model confidence is low
- Rule severity is moderate
- The transaction falls into a borderline risk zone

Review actions may include:

- Step-up authentication
- User identity verification
- Analyst review
- Temporary monitoring
- Request for additional context

## BLOCK Policy

A transaction should be blocked when:

---

Source: docs\audit_policy.md
Relevance score: 0.227
s the action selected?
- Was any analyst review performed?

## Required Audit Fields

Each audit record should preserve:

| Field | Purpose |
|---|---|
| Transaction ID | Identifies the scored transaction |
| User ID | Identifies the account or user |
| Timestamp | Records when the decision was made |
| Final Decision | `ALLOW`, `REVIEW`, or `BLOCK` |
| Fraud Probability | Model-estimated fraud risk |
| Adjusted Risk Score | Risk after rules, anomaly, and confidence adjustments |
| Rule Flags | Deterministic signals triggered by the transaction |
| Anomaly Flag | Whether anomaly detection flagged the transaction |
| Model Confidence | Confidence associated with the model output |
| Decision Reasons | Human-readable explanation |
| Analyst Note | Optional reviewer comment |

## Audit Principles

Audit records should be:

---

Source: docs\risk_policy.md
Relevance score: 0.212
t review
- Temporary monitoring
- Request for additional context

## BLOCK Policy

A transaction should be blocked when:

- Fraud probability is high
- Rule severity is severe
- Anomaly detection combines with elevated model risk
- Account takeover indicators are present
- Blacklisted merchant or high-risk entity indicators appear
- Cost-sensitive adjusted risk crosses the block threshold

Blocked transactions should be escalated into an investigation workflow.

## Audit Requirements

Every decision should preserve:

- Transaction identifier
- User or account identifier
- Final decision
- Fraud probability
- Adjusted risk score
- Rule triggers
- Anomaly flags
- Model confidence
- Decision explanation
- Timestamp
- Analyst notes if available

## Analyst Assistant Boundary

The assistant can:

### Safe Next Step

Recommended next step: keep the transaction blocked, preserve the audit trail, verify user identity, and route the case to fraud review.

Note: This explanation is advisory. It does not override the final FinShield decision.