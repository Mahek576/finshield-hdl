# FinShield Audit Policy

FinShield maintains audit-friendly decision traces for fraud and risk decisions.

The goal of the audit layer is to make every transaction decision explainable, reviewable, and reproducible.

## Audit Objectives

The audit trail should answer:

- What transaction was scored?
- What decision was made?
- Which model and rule signals contributed?
- Was anomaly detection involved?
- What was the model confidence?
- What was the adjusted risk score?
- Why was the action selected?
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

- Traceable
- Human-readable
- Machine-readable
- Stable across reruns when inputs are unchanged
- Safe for analyst review
- Clear about uncertainty

## Assistant Use in Auditing

The analyst assistant may summarize audit records and generate draft analyst notes.

However:

- It cannot modify the original audit record.
- It cannot erase decision evidence.
- It cannot override the final decision.
- It must clearly distinguish between recorded evidence and generated explanation.
- It should say when evidence is insufficient.

## Good Audit Explanation

```text
Decision: BLOCK. The transaction was blocked because fraud probability was high, anomaly detection flagged unusual behavior, and account takeover indicators were present. Recommended action is identity verification and fraud analyst review.
