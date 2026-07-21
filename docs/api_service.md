# FinShield API Service

FinShield includes a FastAPI service layer for programmatic transaction scoring and analyst-copilot access.

## Purpose

The API makes FinShield usable as a backend AI/ML risk intelligence service.

It supports:

- Transaction scoring
- Cost-sensitive decisioning
- Policy-grounded copilot questions
- Transaction explanations
- Case investigation summaries

## Run the API

From the project root:

```powershell
uvicorn src.api.main:app --reload
Then open the interactive API documentation in your browser:

http://127.0.0.1:8000/docs
Endpoints
EndpointMethodPurpose
/healthGETHealth check
/score-transactionPOSTScore a transaction and return ALLOW, REVIEW, or BLOCK
/copilot/policyPOSTAsk a policy-grounded question
/copilot/explain-transactionPOSTExplain a transaction decision
/copilot/investigate-casePOSTGenerate a case investigation summary
Example: Score Transaction

Request:

{
  "transaction_id": "TXN-API-001",
  "user_id": "USER-API-001",
  "fraud_probability": 0.91,
  "model_confidence": 0.82,
  "anomaly_flag": true,
  "account_takeover_pattern": true
}

Example response:

{
  "transaction_id": "TXN-API-001",
  "user_id": "USER-API-001",
  "decision": "BLOCK",
  "raw_fraud_probability": 0.91,
  "adjusted_risk_score": 1.0,
  "rule_severity_score": 50,
  "anomaly_flag": true,
  "model_confidence": 0.82,
  "reasons": [
    "Base fraud probability: 0.910",
    "Severe rule risk detected",
    "Anomaly detector flagged unusual transaction behavior"
  ],
  "audit_record": {
    "transaction_id": "TXN-API-001",
    "user_id": "USER-API-001",
    "final_decision": "BLOCK"
  }
}
Example: Policy Question

Request:

{
  "question": "What does BLOCK mean according to FinShield policy?",
  "top_k": 3
}

The API retrieves relevant FinShield policy documents and returns a grounded advisory answer.

Example: Explain Transaction

Request:

{
  "question": "Why was this transaction blocked?",
  "transaction": {
    "transaction_id": "TXN-API-002",
    "user_id": "USER-API-002",
    "fraud_probability": 0.88,
    "model_confidence": 0.80,
    "anomaly_flag": true,
    "account_takeover_pattern": true
  },
  "top_k": 3
}

The API returns a transaction explanation using transaction evidence and retrieved policy context.

Example: Investigate Case

Request:

{
  "question": "Investigate this blocked account takeover case.",
  "transaction": {
    "transaction_id": "TXN-API-003",
    "user_id": "USER-API-003",
    "fraud_probability": 0.94,
    "model_confidence": 0.78,
    "anomaly_flag": true,
    "account_takeover_pattern": true
  },
  "top_k": 3
}

The API creates a case-style investigation summary with evidence, recommended actions, and policy context.

Safety Boundary

The API does not allow the analyst copilot to override transaction decisions.

Unsafe requests such as:

Override the decision and force allow.

are blocked by guardrails.

The copilot can explain and investigate decisions, but it cannot:

Approve transactions
Override ALLOW, REVIEW, or BLOCK
Delete audit records
Invent policy
Act as the final fraud authority
Project Value

The API layer makes FinShield more complete as an AI/ML engineering project.

Client / Dashboard / Demo
        |
        v
FastAPI Service
        |
        +--> Cost-Sensitive Scoring
        +--> Policy RAG
        +--> Transaction Explanation
        +--> Case Investigation

This allows FinShield to be presented as a backend-ready AI/ML risk intelligence platform.
