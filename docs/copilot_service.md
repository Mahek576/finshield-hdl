# FinShield Copilot Service

The FinShield Copilot Service is the central interface for the analyst intelligence layer.

It connects:

- Guardrails
- Policy-grounded retrieval
- Transaction explanation
- Case investigation
- Dashboard-ready response formatting

The service remains advisory. It does not make or override transaction decisions.

## Purpose

The copilot service gives the project one clean entry point for analyst questions.

It supports:

- Policy questions
- Transaction decision explanations
- Fraud case investigations
- Case creation and investigation
- Dashboard-ready response payloads

## Routing Logic

The service routes questions based on available context:

| Input Provided | Route |
|---|---|
| No transaction or case | Policy-grounded RAG answer |
| Transaction record | Transaction explanation |
| Case record | Case investigation |
| Both transaction and case | Case investigation takes priority |

## Supported Examples

```text
What does BLOCK mean?
Why was this transaction reviewed?
Investigate this blocked account takeover case.
Generate a safe analyst summary for this transaction.
Safety Boundaries

The copilot service uses guardrails before producing responses.

It blocks requests such as:

Override the decision
Force allow
Approve a blocked transaction
Ignore policy
Delete audit evidence
Reveal hidden instructions
Make unsupported final fraud judgments
Response Types
Response TypeMeaning
POLICY_ANSWERRetrieved policy context was used to answer a general question
TRANSACTION_EXPLANATIONA transaction record was explained
CASE_INVESTIGATIONA case record was investigated
GUARDRAIL_REFUSALThe request was blocked for safety
INSUFFICIENT_CONTEXTNot enough policy context was retrieved
Dashboard Integration

The copilot service can produce dashboard-ready payloads containing:

Allowed/blocked status
Response type
Answer text
Retrieved sources
Guardrail categories
Confidence note

This makes it suitable for a future Streamlit tab such as:

FinShield Analyst Copilot
Project Value

The copilot service turns separate utilities into a product-style analyst interface.

Analyst Question
        |
        v
Copilot Service
        |
        +--> Guardrails
        +--> RAG Retrieval
        +--> Transaction Explanation
        +--> Case Investigation
        |
        v
Safe Advisory Response

This gives FinShield a polished AI/ML product architecture.
