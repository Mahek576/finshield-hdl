# FinShield LLM and RAG Design

FinShield includes a policy-grounded analyst intelligence layer.

The purpose of this layer is to help analysts understand fraud decisions, investigate suspicious transactions, and generate structured explanations using retrieved project documents.

## Design Goal

The assistant is not the fraud decision maker.

The core risk decision comes from:

- Fraud model
- Anomaly detection
- Cybersecurity rules
- Cost-sensitive decisioning
- Calibration and monitoring outputs

The assistant explains and investigates these outputs.

## RAG Flow

```text
Analyst Question
        |
        v
Retrieve relevant FinShield documents
        |
        v
Build grounded context
        |
        v
Generate explanation or investigation summary
        |
        v
Return advisory response with policy boundaries
Knowledge Sources

The RAG layer can retrieve from:

docs/risk_policy.md
docs/fraud_playbook.md
docs/audit_policy.md
docs/model_calibration.md
docs/model_monitoring.md
docs/cost_sensitive_decisioning.md
Supported Questions

The assistant may answer:

Why was this transaction blocked?
What does REVIEW mean?
Which evidence supports this case?
What should an analyst do next?
How should anomaly plus low confidence be handled?
What audit fields should be preserved?
How should a high-risk account takeover case be investigated?
Restricted Questions

The assistant should reject or refuse requests to:

Approve a blocked transaction
Override a risk decision
Ignore policy
Delete audit evidence
Reveal hidden instructions
Make unsupported claims
Act as the final fraud authority
Implementation Strategy

The first version uses local retrieval with TF-IDF similarity.

This keeps the system:

Testable
Offline-friendly
Deterministic
Easy to run without external APIs
Suitable for local development
