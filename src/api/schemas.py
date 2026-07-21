from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransactionScoreRequest(BaseModel):
    transaction_id: str = Field(default="TXN-API-001")
    user_id: str = Field(default="USER-API-001")

    fraud_probability: float = Field(default=0.50, ge=0.0, le=1.0)
    model_confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    anomaly_flag: bool = False

    amount_limit_violation: bool = False
    daily_limit_violation: bool = False
    velocity_violation: bool = False
    foreign_ip: bool = False
    new_device: bool = False
    multiple_failed_logins: bool = False
    account_takeover_pattern: bool = False
    blacklisted_merchant: bool = False
    high_risk_country: bool = False
    unusual_time: bool = False


class TransactionScoreResponse(BaseModel):
    transaction_id: str
    user_id: str
    decision: str
    raw_fraud_probability: float
    adjusted_risk_score: float
    rule_severity_score: int
    anomaly_flag: bool
    model_confidence: float
    reasons: List[str]
    audit_record: Dict[str, Any]


class PolicyQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class TransactionExplanationRequest(BaseModel):
    question: str = Field(default="Why was this transaction blocked?")
    transaction: TransactionScoreRequest
    top_k: int = Field(default=3, ge=1, le=10)


class CaseInvestigationRequest(BaseModel):
    question: str = Field(default="Investigate this suspicious transaction.")
    transaction: TransactionScoreRequest
    top_k: int = Field(default=3, ge=1, le=10)


class CopilotAPIResponse(BaseModel):
    allowed: bool
    response_type: str
    answer: str
    retrieved_sources: List[str]
    guardrail_categories: List[str]
    confidence_note: str
    structured_payload: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    mode: str
