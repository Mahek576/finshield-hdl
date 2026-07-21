from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from src.api.schemas import (
    CaseInvestigationRequest,
    CopilotAPIResponse,
    HealthResponse,
    PolicyQuestionRequest,
    TransactionExplanationRequest,
    TransactionScoreRequest,
    TransactionScoreResponse,
)
from src.llm.copilot_service import (
    answer_policy_question,
    create_case_and_investigate,
    explain_transaction,
)
from src.risk.cost_engine import decision_from_transaction_row


APP_VERSION = "1.0.0"


app = FastAPI(
    title="FinShield API",
    description=(
        "AI-powered fintech fraud and risk intelligence API with "
        "cost-sensitive decisioning, case investigation, and policy-grounded copilot support."
    ),
    version=APP_VERSION,
)


def transaction_request_to_record(request: TransactionScoreRequest) -> Dict[str, Any]:
    return request.model_dump()


def score_transaction_record(record: Dict[str, Any]) -> Dict[str, Any]:
    result = decision_from_transaction_row(record)

    final_decision = result.decision.value

    audit_record = {
        "transaction_id": record.get("transaction_id", "UNKNOWN_TRANSACTION"),
        "user_id": record.get("user_id", "UNKNOWN_USER"),
        "final_decision": final_decision,
        "fraud_probability": result.raw_fraud_probability,
        "adjusted_risk_score": result.adjusted_risk_score,
        "rule_severity_score": result.rule_severity_score,
        "anomaly_flag": result.anomaly_flag,
        "model_confidence": result.model_confidence,
        "decision_reasons": result.reasons,
    }

    return {
        "transaction_id": audit_record["transaction_id"],
        "user_id": audit_record["user_id"],
        "decision": final_decision,
        "raw_fraud_probability": result.raw_fraud_probability,
        "adjusted_risk_score": result.adjusted_risk_score,
        "rule_severity_score": result.rule_severity_score,
        "anomaly_flag": result.anomaly_flag,
        "model_confidence": result.model_confidence,
        "reasons": result.reasons,
        "audit_record": audit_record,
    }


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="FinShield API",
        version=APP_VERSION,
        mode="AI/ML risk intelligence",
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="FinShield API",
        version=APP_VERSION,
        mode="AI/ML risk intelligence",
    )


@app.post("/score-transaction", response_model=TransactionScoreResponse)
def score_transaction(request: TransactionScoreRequest) -> TransactionScoreResponse:
    record = transaction_request_to_record(request)
    payload = score_transaction_record(record)
    return TransactionScoreResponse(**payload)


@app.post("/copilot/policy", response_model=CopilotAPIResponse)
def copilot_policy(request: PolicyQuestionRequest) -> CopilotAPIResponse:
    response = answer_policy_question(
        question=request.question,
        top_k=request.top_k,
    )

    return CopilotAPIResponse(
        allowed=response.allowed,
        response_type=response.response_type.value,
        answer=response.answer,
        retrieved_sources=response.retrieved_sources,
        guardrail_categories=response.guardrail_categories,
        confidence_note=response.confidence_note,
        structured_payload=response.structured_payload,
    )


@app.post("/copilot/explain-transaction", response_model=CopilotAPIResponse)
def copilot_explain_transaction(request: TransactionExplanationRequest) -> CopilotAPIResponse:
    record = transaction_request_to_record(request.transaction)
    score_payload = score_transaction_record(record)

    enriched_record = {
        **record,
        "final_decision": score_payload["decision"],
        "fraud_probability": score_payload["raw_fraud_probability"],
        "risk_score": score_payload["adjusted_risk_score"],
        "model_confidence": score_payload["model_confidence"],
        "anomaly_flag": score_payload["anomaly_flag"],
    }

    response = explain_transaction(
        question=request.question,
        transaction_record=enriched_record,
        top_k=request.top_k,
    )

    return CopilotAPIResponse(
        allowed=response.allowed,
        response_type=response.response_type.value,
        answer=response.answer,
        retrieved_sources=response.retrieved_sources,
        guardrail_categories=response.guardrail_categories,
        confidence_note=response.confidence_note,
        structured_payload=response.structured_payload,
    )


@app.post("/copilot/investigate-case", response_model=CopilotAPIResponse)
def copilot_investigate_case(request: CaseInvestigationRequest) -> CopilotAPIResponse:
    record = transaction_request_to_record(request.transaction)
    score_payload = score_transaction_record(record)

    enriched_record = {
        **record,
        "final_decision": score_payload["decision"],
        "fraud_probability": score_payload["raw_fraud_probability"],
        "risk_score": score_payload["adjusted_risk_score"],
        "model_confidence": score_payload["model_confidence"],
        "anomaly_flag": score_payload["anomaly_flag"],
    }

    response = create_case_and_investigate(
        question=request.question,
        transaction_record=enriched_record,
        top_k=request.top_k,
    )

    return CopilotAPIResponse(
        allowed=response.allowed,
        response_type=response.response_type.value,
        answer=response.answer,
        retrieved_sources=response.retrieved_sources,
        guardrail_categories=response.guardrail_categories,
        confidence_note=response.confidence_note,
        structured_payload=response.structured_payload,
    )
