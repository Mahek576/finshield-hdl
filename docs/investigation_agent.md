# FinShield Investigation Agent

FinShield includes an investigation agent that converts fraud cases into structured, evidence-grounded investigation summaries.

The investigation agent connects:

- Case management
- Policy-grounded retrieval
- Guardrails
- Explanation agent
- Analyst note generation
- Report export

It does not make or override fraud decisions. It investigates and explains decisions already produced by the FinShield AI/ML risk pipeline.

## Purpose

The investigation agent helps analysts answer:

- What is the case about?
- Why was the transaction reviewed or blocked?
- Which evidence supports the decision?
- Does the case suggest account takeover?
- What should the analyst do next?
- What policy context applies?
- What should be written in the investigation report?

## Inputs

The investigation agent can accept:

- A transaction record
- A fraud case object
- Retrieved policy documents
- Analyst question
- Rule, model, anomaly, and confidence evidence

## Outputs

The investigation agent produces:

- Investigation summary
- Investigation focus areas
- Recommended actions
- Analyst note
- Retrieved source list
- Markdown investigation report
- Batch investigation summary

## Investigation Focus Areas

The agent may classify a case into focus areas such as:

| Focus Area | Meaning |
|---|---|
| `blocked_transaction` | Transaction was blocked |
| `high_priority_case` | Case requires urgent review |
| `high_model_risk` | Fraud probability is high |
| `block_level_adjusted_risk` | Adjusted risk score crosses block-level risk |
| `anomaly_investigation` | Anomaly detection was involved |
| `account_takeover_review` | Evidence suggests possible account takeover |
| `low_confidence_review` | Model confidence is low |
| `rule_trigger_review` | Deterministic rule evidence exists |

## Recommended Actions

Actions may include:

- Keep transaction blocked
- Route for step-up authentication
- Verify user identity
- Review recent account activity
- Compare with user behavior history
- Preserve audit trail
- Escalate to fraud operations

## Guardrails

The investigation agent follows strict safety boundaries:

- It cannot approve blocked transactions.
- It cannot override ALLOW, REVIEW, or BLOCK decisions.
- It cannot delete audit evidence.
- It cannot invent missing evidence.
- It cannot act as the final fraud authority.

Unsafe analyst requests are blocked and redirected toward safe alternatives.

## Offline First

The first version is deterministic and offline.

It uses structured case evidence and local policy retrieval. This keeps the module:

- Testable
- Reproducible
- Easy to run locally
- Independent of external APIs

A future version can connect the generated context to an external LLM provider while preserving the same policy, retrieval, and guardrail structure.

## Project Value

The investigation agent turns FinShield into a more complete fraud operations platform.

```text
Suspicious Transaction
        |
        v
Fraud Case
        |
        v
Evidence + Policy Retrieval
        |
        v
Investigation Summary
        |
        v
Analyst Review / Report / Resolution
