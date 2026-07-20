# Cost-Sensitive Risk Decisioning

FinShield uses cost-sensitive decisioning to convert model, anomaly, and rule evidence into practical transaction actions.

The final decision is not based only on raw model accuracy. In fintech fraud systems, different mistakes have different business impacts.

## Why Cost-Sensitive Decisioning Matters

A fraud model can be statistically accurate but operationally weak if it does not consider the cost of different errors.

| Error Type | Meaning | Impact |
|---|---|---|
| False Positive | Genuine transaction is blocked | Customer friction |
| False Negative | Fraud transaction is allowed | Financial loss |
| Review Decision | Transaction requires manual/security review | Analyst workload |

FinShield therefore uses three actions:

| Decision | Meaning |
|---|---|
| `ALLOW` | Transaction appears safe enough to pass |
| `REVIEW` | Transaction is suspicious and needs step-up authentication or analyst review |
| `BLOCK` | Transaction risk is high enough to stop immediately |

## Evidence Used

The cost-sensitive decision engine uses:

- Supervised model fraud probability
- Model confidence
- Anomaly detector output
- Rule severity score
- Business risk thresholds

## Rule Severity

Deterministic cybersecurity and risk rules are converted into a severity score from 0 to 100.

Examples of rule signals include:

- Amount limit violation
- Daily limit violation
- Transaction velocity violation
- Foreign IP indicator
- New device indicator
- Multiple failed logins
- Account takeover pattern
- Blacklisted merchant
- High-risk country
- Unusual transaction time

## Risk Adjustment

The raw model fraud probability is adjusted upward when additional risk evidence is present.

Examples:

- Anomaly detected
- Severe rule violation
- Low model confidence
- Anomaly combined with elevated fraud probability

This creates a more practical risk score for operational decision-making.

## Decision Policy

Default thresholds:

| Threshold | Value |
|---|---|
| Review threshold | `0.35` |
| Block threshold | `0.75` |

Default decision behavior:

| Adjusted Risk Score | Decision |
|---|---|
| `< 0.35` | `ALLOW` |
| `0.35 - 0.749` | `REVIEW` |
| `>= 0.75` | `BLOCK` |

## Auditability

Each decision returns:

- Final decision
- Raw fraud probability
- Adjusted risk score
- Rule severity score
- Anomaly flag
- Model confidence
- Expected allow/review/block costs
- Human-readable reasons

This makes the decision trace suitable for audit logs, dashboards, and analyst investigation reports.

## Project Value

This module strengthens FinShield by making it more than a standard fraud classifier.

It turns prediction output into an explainable business decision:

```text
ML probability + anomaly evidence + rule severity + confidence
        |
        v
Cost-sensitive decision engine
        |
        v
ALLOW / REVIEW / BLOCK
