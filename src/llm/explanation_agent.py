from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence

from src.llm.guardrails import check_llm_request_safety
from src.llm.rag_retriever import LocalRAGRetriever, RetrievalResult


@dataclass(frozen=True)
class EvidenceSummary:
    transaction_id: str
    user_id: str
    final_decision: str
    risk_score: float
    fraud_probability: float
    model_confidence: float
    anomaly_flag: bool
    triggered_rules: List[str]
    evidence_points: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExplanationResult:
    allowed: bool
    response_type: str
    explanation: str
    retrieved_sources: List[str]
    evidence_summary: Optional[EvidenceSummary]
    guardrail_categories: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "response_type": self.response_type,
            "explanation": self.explanation,
            "retrieved_sources": self.retrieved_sources,
            "evidence_summary": None
            if self.evidence_summary is None
            else self.evidence_summary.to_dict(),
            "guardrail_categories": self.guardrail_categories,
        }


RULE_DESCRIPTIONS: Dict[str, str] = {
    "amount_limit_violation": "Transaction amount exceeded the configured risk threshold.",
    "daily_limit_violation": "Daily transaction activity exceeded the configured threshold.",
    "velocity_violation": "Transaction velocity is higher than expected.",
    "foreign_ip": "Transaction context includes a foreign IP or unusual location signal.",
    "new_device": "Transaction was initiated from a new or unfamiliar device.",
    "multiple_failed_logins": "Multiple failed login attempts were observed.",
    "account_takeover_pattern": "Combined signals suggest possible account takeover behavior.",
    "blacklisted_merchant": "Merchant appears in a blocked or high-risk merchant list.",
    "high_risk_country": "Transaction is associated with a high-risk country or region.",
    "unusual_time": "Transaction occurred at an unusual time for the user.",
}


def _safe_str(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "fraud", "anomaly"}
    return bool(value)


def _clip_probability(value: Any) -> float:
    return max(0.0, min(1.0, _safe_float(value, 0.0)))


def _get_first(record: Mapping[str, Any], keys: Sequence[str], default: Any) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return default


def extract_triggered_rules(record: Mapping[str, Any]) -> List[str]:
    rules: List[str] = []

    for rule_name in RULE_DESCRIPTIONS:
        if _safe_bool(record.get(rule_name, False)):
            rules.append(rule_name)

    return rules


def summarize_transaction_evidence(record: Mapping[str, Any]) -> EvidenceSummary:
    transaction_id = _safe_str(
        _get_first(record, ["transaction_id", "txn_id", "id"], "UNKNOWN_TRANSACTION"),
        "UNKNOWN_TRANSACTION",
    )
    user_id = _safe_str(
        _get_first(record, ["user_id", "customer_id", "account_id"], "UNKNOWN_USER"),
        "UNKNOWN_USER",
    )

    final_decision = _safe_str(
        _get_first(record, ["final_decision", "decision", "final_action"], "REVIEW"),
        "REVIEW",
    ).upper()

    fraud_probability = _clip_probability(
        _get_first(
            record,
            ["fraud_probability", "ml_fraud_probability", "fraud_score"],
            0.0,
        )
    )

    risk_score = _clip_probability(
        _get_first(
            record,
            ["adjusted_risk_score", "risk_score", "final_risk_score"],
            fraud_probability,
        )
    )

    model_confidence = _clip_probability(
        _get_first(
            record,
            ["model_confidence", "ml_confidence", "confidence_score"],
            1.0,
        )
    )

    anomaly_flag = _safe_bool(
        _get_first(
            record,
            ["anomaly_flag", "is_anomaly", "anomaly_detected"],
            False,
        )
    )

    triggered_rules = extract_triggered_rules(record)

    evidence_points: List[str] = []

    if fraud_probability >= 0.75:
        evidence_points.append(f"Fraud probability is high at {fraud_probability:.3f}.")
    elif fraud_probability >= 0.35:
        evidence_points.append(f"Fraud probability is elevated at {fraud_probability:.3f}.")
    else:
        evidence_points.append(f"Fraud probability is low at {fraud_probability:.3f}.")

    if risk_score >= 0.75:
        evidence_points.append(f"Adjusted risk score is block-level at {risk_score:.3f}.")
    elif risk_score >= 0.35:
        evidence_points.append(f"Adjusted risk score is review-level at {risk_score:.3f}.")
    else:
        evidence_points.append(f"Adjusted risk score is low at {risk_score:.3f}.")

    if anomaly_flag:
        evidence_points.append("Anomaly detection flagged unusual transaction behavior.")

    if model_confidence < 0.55:
        evidence_points.append(f"Model confidence is low at {model_confidence:.3f}.")
    else:
        evidence_points.append(f"Model confidence is acceptable at {model_confidence:.3f}.")

    for rule in triggered_rules:
        evidence_points.append(RULE_DESCRIPTIONS[rule])

    return EvidenceSummary(
        transaction_id=transaction_id,
        user_id=user_id,
        final_decision=final_decision,
        risk_score=risk_score,
        fraud_probability=fraud_probability,
        model_confidence=model_confidence,
        anomaly_flag=anomaly_flag,
        triggered_rules=triggered_rules,
        evidence_points=evidence_points,
    )


def _sources_from_results(results: Sequence[RetrievalResult]) -> List[str]:
    seen = set()
    sources: List[str] = []

    for result in results:
        source = result.chunk.source_path
        if source not in seen:
            sources.append(source)
            seen.add(source)

    return sources


def _policy_context_from_results(results: Sequence[RetrievalResult]) -> str:
    if not results:
        return "No retrieved policy context was available."

    sections: List[str] = []

    for result in results:
        sections.append(
            f"Source: {result.chunk.source_path}\n"
            f"Relevance score: {result.score:.3f}\n"
            f"{result.chunk.text.strip()}"
        )

    return "\n\n---\n\n".join(sections)


def generate_transaction_explanation(
    record: Mapping[str, Any],
    retriever: Optional[LocalRAGRetriever] = None,
    user_question: str = "Explain this FinShield transaction decision.",
    top_k: int = 3,
) -> ExplanationResult:
    """
    Generate a safe, grounded explanation for one transaction or case record.

    This is intentionally offline and deterministic. It does not call an external
    LLM. It prepares the same evidence-grounded explanation style that can later
    be connected to an LLM provider.
    """

    safety = check_llm_request_safety(user_question)

    if not safety.allowed:
        return ExplanationResult(
            allowed=False,
            response_type="guardrail_refusal",
            explanation=(
                "I cannot process this request because it attempts to bypass "
                "FinShield decision, policy, or safety boundaries. "
                f"Safe alternative: {safety.safe_alternative}"
            ),
            retrieved_sources=[],
            evidence_summary=None,
            guardrail_categories=safety.categories,
        )

    evidence = summarize_transaction_evidence(record)

    retrieval_results: List[RetrievalResult] = []
    if retriever is not None:
        retrieval_query = (
            f"{user_question} {evidence.final_decision} "
            f"fraud probability anomaly model confidence rule policy audit"
        )
        retrieval_results = retriever.query(retrieval_query, top_k=top_k)

    policy_context = _policy_context_from_results(retrieval_results)
    retrieved_sources = _sources_from_results(retrieval_results)

    explanation = build_explanation_text(
        evidence=evidence,
        policy_context=policy_context,
        user_question=user_question,
    )

    return ExplanationResult(
        allowed=True,
        response_type="transaction_explanation",
        explanation=explanation,
        retrieved_sources=retrieved_sources,
        evidence_summary=evidence,
        guardrail_categories=[],
    )


def build_explanation_text(
    evidence: EvidenceSummary,
    policy_context: str,
    user_question: str,
) -> str:
    decision = evidence.final_decision

    if decision == "BLOCK":
        decision_sentence = (
            "FinShield blocked this transaction because the combined evidence "
            "indicates high operational fraud risk."
        )
        next_step = (
            "Recommended next step: keep the transaction blocked, preserve the audit trail, "
            "verify user identity, and route the case to fraud review."
        )
    elif decision == "REVIEW":
        decision_sentence = (
            "FinShield routed this transaction to review because the evidence indicates "
            "elevated or uncertain risk."
        )
        next_step = (
            "Recommended next step: request step-up authentication or analyst review "
            "before allowing the transaction."
        )
    elif decision == "ALLOW":
        decision_sentence = (
            "FinShield allowed this transaction because the available evidence does not "
            "cross review or block thresholds."
        )
        next_step = (
            "Recommended next step: retain the normal audit trace and continue monitoring."
        )
    else:
        decision_sentence = (
            "FinShield produced a decision that should be reviewed against the risk policy."
        )
        next_step = (
            "Recommended next step: inspect the audit evidence and verify policy alignment."
        )

    triggered_rules = (
        ", ".join(evidence.triggered_rules)
        if evidence.triggered_rules
        else "No deterministic rule flags were triggered."
    )

    evidence_lines = "\n".join(f"- {point}" for point in evidence.evidence_points)

    return "\n".join(
        [
            "## FinShield Analyst Explanation",
            "",
            f"Analyst question: {user_question}",
            "",
            "### Decision Summary",
            "",
            f"- Transaction ID: `{evidence.transaction_id}`",
            f"- User ID: `{evidence.user_id}`",
            f"- Final Decision: `{evidence.final_decision}`",
            f"- Fraud Probability: `{evidence.fraud_probability:.3f}`",
            f"- Adjusted Risk Score: `{evidence.risk_score:.3f}`",
            f"- Model Confidence: `{evidence.model_confidence:.3f}`",
            f"- Anomaly Flag: `{evidence.anomaly_flag}`",
            f"- Triggered Rules: {triggered_rules}",
            "",
            "### Explanation",
            "",
            decision_sentence,
            "",
            "### Evidence",
            "",
            evidence_lines,
            "",
            "### Retrieved Policy Context",
            "",
            policy_context,
            "",
            "### Safe Next Step",
            "",
            next_step,
            "",
            "Note: This explanation is advisory. It does not override the final FinShield decision.",
        ]
    )


def generate_batch_explanations(
    records: Sequence[Mapping[str, Any]],
    retriever: Optional[LocalRAGRetriever] = None,
    user_question: str = "Explain this FinShield transaction decision.",
    top_k: int = 3,
) -> List[ExplanationResult]:
    return [
        generate_transaction_explanation(
            record=record,
            retriever=retriever,
            user_question=user_question,
            top_k=top_k,
        )
        for record in records
    ]


def generate_analyst_note(record: Mapping[str, Any]) -> str:
    evidence = summarize_transaction_evidence(record)

    top_evidence = evidence.evidence_points[:4]
    evidence_text = " ".join(top_evidence)

    if evidence.final_decision == "BLOCK":
        action = "Keep blocked and escalate for fraud review."
    elif evidence.final_decision == "REVIEW":
        action = "Route for step-up authentication or analyst review."
    else:
        action = "Allow with standard audit monitoring."

    return (
        f"Transaction {evidence.transaction_id} for user {evidence.user_id} received "
        f"a final decision of {evidence.final_decision}. "
        f"Fraud probability={evidence.fraud_probability:.3f}, "
        f"adjusted risk={evidence.risk_score:.3f}, "
        f"model confidence={evidence.model_confidence:.3f}. "
        f"Evidence: {evidence_text} "
        f"Recommended action: {action}"
    )
