from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

from src.cases.case_manager import (
    CaseDecision,
    CasePriority,
    FraudCase,
    case_to_markdown,
    create_case_from_record,
)
from src.llm.explanation_agent import (
    ExplanationResult,
    generate_analyst_note,
    generate_transaction_explanation,
)
from src.llm.guardrails import check_llm_request_safety
from src.llm.rag_retriever import LocalRAGRetriever, RetrievalResult


@dataclass(frozen=True)
class InvestigationResult:
    allowed: bool
    response_type: str
    case_id: str
    transaction_id: str
    user_id: str
    decision: str
    priority: str
    status: str
    investigation_focus: List[str]
    summary: str
    recommended_actions: List[str]
    analyst_note: str
    retrieved_sources: List[str]
    guardrail_categories: List[str]
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BatchInvestigationSummary:
    total_cases: int
    critical_cases: int
    high_priority_cases: int
    review_cases: int
    blocked_cases: int
    top_focus_areas: Dict[str, int]
    results: List[InvestigationResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "critical_cases": self.critical_cases,
            "high_priority_cases": self.high_priority_cases,
            "review_cases": self.review_cases,
            "blocked_cases": self.blocked_cases,
            "top_focus_areas": self.top_focus_areas,
            "results": [result.to_dict() for result in self.results],
        }


def _case_from_input(case_or_record: FraudCase | Mapping[str, Any]) -> FraudCase:
    if isinstance(case_or_record, FraudCase):
        return case_or_record

    return create_case_from_record(case_or_record)


def _sources_from_results(results: Sequence[RetrievalResult]) -> List[str]:
    seen = set()
    sources: List[str] = []

    for result in results:
        source = result.chunk.source_path
        if source not in seen:
            sources.append(source)
            seen.add(source)

    return sources


def _build_case_record(case: FraudCase) -> Dict[str, Any]:
    record = {
        "transaction_id": case.transaction_id,
        "user_id": case.user_id,
        "final_decision": case.decision.value,
        "risk_score": case.risk_score,
        "fraud_probability": case.fraud_probability,
        "model_confidence": case.model_confidence,
        "anomaly_flag": case.anomaly_flag,
    }

    for item in case.evidence:
        source = str(item.source)
        if source:
            record[source] = True

    return record


def infer_investigation_focus(case: FraudCase) -> List[str]:
    focus: List[str] = []
    evidence_types = {item.evidence_type for item in case.evidence}
    evidence_sources = {str(item.source) for item in case.evidence}

    if case.decision == CaseDecision.BLOCK:
        focus.append("blocked_transaction")

    if case.priority in {CasePriority.HIGH, CasePriority.CRITICAL}:
        focus.append("high_priority_case")

    if case.fraud_probability >= 0.75:
        focus.append("high_model_risk")
    elif case.fraud_probability >= 0.35:
        focus.append("elevated_model_risk")

    if case.risk_score >= 0.75:
        focus.append("block_level_adjusted_risk")
    elif case.risk_score >= 0.35:
        focus.append("review_level_adjusted_risk")

    if case.anomaly_flag or "anomaly" in evidence_types:
        focus.append("anomaly_investigation")

    if "account_takeover" in evidence_types or {
        "foreign_ip",
        "new_device",
        "multiple_failed_logins",
        "account_takeover_pattern",
    }.intersection(evidence_sources):
        focus.append("account_takeover_review")

    if "model_confidence" in evidence_types or case.model_confidence < 0.55:
        focus.append("low_confidence_review")

    if "rule" in evidence_types:
        focus.append("rule_trigger_review")

    if not focus:
        focus.append("standard_audit_review")

    return sorted(set(focus))


def build_case_context(case: FraudCase) -> str:
    evidence_lines = []

    for item in case.evidence:
        evidence_lines.append(
            f"- [{item.evidence_type}] {item.description} "
            f"(severity={item.severity}/100, source={item.source})"
        )

    if not evidence_lines:
        evidence_lines.append("- No additional evidence items recorded.")

    return "\n".join(
        [
            f"Case ID: {case.case_id}",
            f"Transaction ID: {case.transaction_id}",
            f"User ID: {case.user_id}",
            f"Decision: {case.decision.value}",
            f"Priority: {case.priority.value}",
            f"Status: {case.status.value}",
            f"Risk Score: {case.risk_score:.3f}",
            f"Fraud Probability: {case.fraud_probability:.3f}",
            f"Model Confidence: {case.model_confidence:.3f}",
            f"Anomaly Flag: {case.anomaly_flag}",
            "Evidence:",
            *evidence_lines,
            f"Recommended Action: {case.recommended_action}",
            f"Analyst Note: {case.analyst_note or 'No analyst note recorded.'}",
        ]
    )


def build_retrieval_query(case: FraudCase, analyst_question: str) -> str:
    focus = " ".join(infer_investigation_focus(case))

    return (
        f"{analyst_question} "
        f"decision {case.decision.value} priority {case.priority.value} "
        f"fraud probability anomaly risk policy audit investigation {focus}"
    )


def generate_recommended_actions(case: FraudCase, focus: Sequence[str]) -> List[str]:
    actions: List[str] = []

    if case.decision == CaseDecision.BLOCK:
        actions.append("Keep the transaction blocked while the investigation is open.")

    if case.decision == CaseDecision.REVIEW:
        actions.append("Route the transaction to step-up authentication or analyst review.")

    if "account_takeover_review" in focus:
        actions.append("Verify user identity and review recent login and device activity.")

    if "anomaly_investigation" in focus:
        actions.append("Compare this transaction with recent user behavior and anomaly history.")

    if "low_confidence_review" in focus:
        actions.append("Avoid fully automated resolution because model confidence is low.")

    if "high_model_risk" in focus or "block_level_adjusted_risk" in focus:
        actions.append("Escalate to fraud operations if evidence remains consistent after review.")

    if not actions:
        actions.append("Preserve the audit trace and continue monitoring.")

    if case.recommended_action:
        actions.append(case.recommended_action)

    deduped: List[str] = []
    seen = set()

    for action in actions:
        if action not in seen:
            deduped.append(action)
            seen.add(action)

    return deduped


def build_investigation_summary_text(
    case: FraudCase,
    focus: Sequence[str],
    explanation: ExplanationResult,
    retrieved_context: str,
    recommended_actions: Sequence[str],
) -> str:
    focus_text = ", ".join(focus)
    actions_text = "\n".join(f"- {action}" for action in recommended_actions)

    evidence_count = len(case.evidence)

    if case.decision == CaseDecision.BLOCK:
        opening = (
            "This case should be treated as a blocked high-risk transaction investigation."
        )
    elif case.decision == CaseDecision.REVIEW:
        opening = (
            "This case should be treated as a review workflow requiring additional verification."
        )
    else:
        opening = (
            "This case appears lower risk, but it has been retained for audit or monitoring review."
        )

    return "\n".join(
        [
            f"# FinShield Investigation Summary: {case.case_id}",
            "",
            "## Overview",
            "",
            opening,
            "",
            f"- Transaction ID: `{case.transaction_id}`",
            f"- User ID: `{case.user_id}`",
            f"- Decision: `{case.decision.value}`",
            f"- Priority: `{case.priority.value}`",
            f"- Status: `{case.status.value}`",
            f"- Risk Score: `{case.risk_score:.3f}`",
            f"- Fraud Probability: `{case.fraud_probability:.3f}`",
            f"- Model Confidence: `{case.model_confidence:.3f}`",
            f"- Anomaly Flag: `{case.anomaly_flag}`",
            f"- Evidence Items: `{evidence_count}`",
            f"- Investigation Focus: `{focus_text}`",
            "",
            "## Evidence-Grounded Explanation",
            "",
            explanation.explanation if explanation.allowed else "Explanation was blocked by guardrails.",
            "",
            "## Recommended Actions",
            "",
            actions_text,
            "",
            "## Retrieved Policy Context Used",
            "",
            retrieved_context if retrieved_context.strip() else "No retrieved policy context was available.",
            "",
            "## Safety Boundary",
            "",
            "This investigation summary is advisory. It does not override FinShield's final decision.",
        ]
    )


def generate_investigation_summary(
    case_or_record: FraudCase | Mapping[str, Any],
    retriever: Optional[LocalRAGRetriever] = None,
    analyst_question: str = "Investigate this FinShield case.",
    top_k: int = 3,
) -> InvestigationResult:
    safety = check_llm_request_safety(analyst_question)

    case = _case_from_input(case_or_record)

    if not safety.allowed:
        return InvestigationResult(
            allowed=False,
            response_type="guardrail_refusal",
            case_id=case.case_id,
            transaction_id=case.transaction_id,
            user_id=case.user_id,
            decision=case.decision.value,
            priority=case.priority.value,
            status=case.status.value,
            investigation_focus=[],
            summary=(
                "This investigation request was blocked by FinShield guardrails. "
                f"Reason: {safety.reason} Safe alternative: {safety.safe_alternative}"
            ),
            recommended_actions=[
                safety.safe_alternative
                or "Ask for an explanation or policy-grounded investigation summary instead."
            ],
            analyst_note="",
            retrieved_sources=[],
            guardrail_categories=safety.categories,
            explanation=None,
        )

    focus = infer_investigation_focus(case)
    case_record = _build_case_record(case)

    retrieval_results: List[RetrievalResult] = []
    retrieved_context = ""

    if retriever is not None:
        retrieval_results = retriever.query(
            question=build_retrieval_query(case, analyst_question),
            top_k=top_k,
        )

        retrieved_context = "\n\n---\n\n".join(
            f"Source: {result.chunk.source_path}\n"
            f"Score: {result.score:.3f}\n"
            f"{result.chunk.text.strip()}"
            for result in retrieval_results
        )

    explanation = generate_transaction_explanation(
        record=case_record,
        retriever=retriever,
        user_question=analyst_question,
        top_k=top_k,
    )

    recommended_actions = generate_recommended_actions(case, focus)
    analyst_note = generate_analyst_note(case_record)

    summary = build_investigation_summary_text(
        case=case,
        focus=focus,
        explanation=explanation,
        retrieved_context=retrieved_context,
        recommended_actions=recommended_actions,
    )

    return InvestigationResult(
        allowed=True,
        response_type="investigation_summary",
        case_id=case.case_id,
        transaction_id=case.transaction_id,
        user_id=case.user_id,
        decision=case.decision.value,
        priority=case.priority.value,
        status=case.status.value,
        investigation_focus=list(focus),
        summary=summary,
        recommended_actions=list(recommended_actions),
        analyst_note=analyst_note,
        retrieved_sources=_sources_from_results(retrieval_results),
        guardrail_categories=[],
        explanation=explanation.explanation if explanation.allowed else None,
    )


def generate_batch_investigation_summary(
    cases_or_records: Iterable[FraudCase | Mapping[str, Any]],
    retriever: Optional[LocalRAGRetriever] = None,
    analyst_question: str = "Investigate this FinShield case.",
    top_k: int = 3,
) -> BatchInvestigationSummary:
    results = [
        generate_investigation_summary(
            case_or_record=item,
            retriever=retriever,
            analyst_question=analyst_question,
            top_k=top_k,
        )
        for item in cases_or_records
    ]

    critical_cases = sum(1 for result in results if result.priority == "CRITICAL")
    high_priority_cases = sum(1 for result in results if result.priority == "HIGH")
    review_cases = sum(1 for result in results if result.decision == "REVIEW")
    blocked_cases = sum(1 for result in results if result.decision == "BLOCK")

    focus_counts: Dict[str, int] = {}

    for result in results:
        for focus in result.investigation_focus:
            focus_counts[focus] = focus_counts.get(focus, 0) + 1

    return BatchInvestigationSummary(
        total_cases=len(results),
        critical_cases=critical_cases,
        high_priority_cases=high_priority_cases,
        review_cases=review_cases,
        blocked_cases=blocked_cases,
        top_focus_areas=dict(sorted(focus_counts.items())),
        results=results,
    )


def investigation_result_to_markdown(result: InvestigationResult) -> str:
    if result.allowed:
        return result.summary

    return "\n".join(
        [
            f"# FinShield Investigation Request Blocked: {result.case_id}",
            "",
            result.summary,
            "",
            "## Guardrail Categories",
            "",
            ", ".join(result.guardrail_categories) if result.guardrail_categories else "None",
        ]
    )


def save_investigation_report(
    result: InvestigationResult,
    output_dir: str | Path = "results/investigations",
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / f"{result.case_id}_investigation.md"
    file_path.write_text(investigation_result_to_markdown(result), encoding="utf-8")

    return file_path


def save_batch_investigation_summary(
    summary: BatchInvestigationSummary,
    output_dir: str | Path = "results/investigations",
    prefix: str = "batch_investigation",
) -> Dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / f"{prefix}_results.csv"
    summary_path = output_path / f"{prefix}_summary.csv"

    pd.DataFrame([result.to_dict() for result in summary.results]).to_csv(csv_path, index=False)

    pd.DataFrame(
        [
            {
                "total_cases": summary.total_cases,
                "critical_cases": summary.critical_cases,
                "high_priority_cases": summary.high_priority_cases,
                "review_cases": summary.review_cases,
                "blocked_cases": summary.blocked_cases,
                "top_focus_areas": summary.top_focus_areas,
            }
        ]
    ).to_csv(summary_path, index=False)

    return {
        "results_csv": csv_path,
        "summary_csv": summary_path,
    }


def case_report_with_investigation(case: FraudCase, investigation: InvestigationResult) -> str:
    return "\n".join(
        [
            case_to_markdown(case),
            "",
            "---",
            "",
            investigation_result_to_markdown(investigation),
        ]
    )
