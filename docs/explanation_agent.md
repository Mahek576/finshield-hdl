# FinShield Explanation Agent

FinShield includes an explanation agent that converts transaction risk evidence into analyst-friendly explanations.

The explanation agent is part of the policy-grounded analyst intelligence layer.

It does not make fraud decisions. It explains decisions that were already produced by the FinShield AI/ML risk pipeline.

## Purpose

The explanation agent helps answer:

- Why was this transaction blocked?
- Why was this transaction sent to review?
- Which evidence supports the decision?
- Which rules were triggered?
- Was anomaly detection involved?
- What should the analyst do next?

## Inputs

The explanation agent can use:

- Transaction ID
- User ID
- Final decision
- Fraud probability
- Adjusted risk score
- Model confidence
- Anomaly flag
- Triggered rule flags
- Retrieved policy context

## Outputs

The explanation agent produces:

- Decision summary
- Evidence summary
- Retrieved policy context
- Safe next-step recommendation
- Analyst note draft

## Guardrails

The explanation agent follows FinShield safety boundaries:

- It cannot override risk decisions.
- It cannot approve blocked transactions.
- It cannot delete audit evidence.
- It cannot invent policy.
- It must say when evidence is insufficient.
- It remains advisory only.

## Offline First Design

The first version is deterministic and offline.

It does not require an external LLM API.

This allows the project to remain:

- Testable
- Stable
- Reproducible
- Easy to run locally

A future version can connect the generated prompt and retrieved context to an external LLM provider while preserving the same retrieval and guardrail architecture.

## Example Output

```text
FinShield blocked this transaction because the combined evidence indicates high operational fraud risk.

Evidence:
- Fraud probability is high at 0.910.
- Adjusted risk score is block-level at 0.940.
- Anomaly detection flagged unusual transaction behavior.
- Transaction velocity is higher than expected.

Recommended next step:
Keep the transaction blocked, preserve the audit trail, verify user identity, and route the case to fraud review.
Project Value

The explanation agent makes FinShield more than a prediction engine.

Risk decision
        |
        v
Evidence extraction
        |
        v
Policy-grounded explanation
        |
        v
Analyst note / case report / dashboard explanation

This improves explainability, auditability, and product completeness.
