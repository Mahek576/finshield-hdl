# FinShield Risk Policy

FinShield uses a structured risk policy to convert transaction evidence into explainable decisions.

The platform supports three final decision levels:

| Decision | Meaning |
|---|---|
| `ALLOW` | Transaction appears safe enough to proceed |
| `REVIEW` | Transaction requires step-up authentication or analyst review |
| `BLOCK` | Transaction risk is high enough to stop immediately |

## Decision Principles

FinShield decisions are based on combined evidence from:

- Supervised fraud model probability
- Anomaly detection
- Cybersecurity and transaction rules
- Model confidence
- Cost-sensitive risk thresholds
- Audit evidence

The analyst assistant is advisory only. It can explain, summarize, and help investigate a decision, but it cannot approve, block, reverse, or override transaction decisions.

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

- Explain why a transaction was reviewed or blocked
- Summarize policy context
- Generate analyst notes
- Summarize case evidence
- Answer questions using retrieved policy documents

The assistant cannot:

- Override FinShield decisions
- Approve blocked transactions
- Change transaction status directly
- Invent policy
- Ignore retrieved context
- Act as the final fraud authority
