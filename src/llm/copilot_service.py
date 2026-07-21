from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from src.cases.case_manager import FraudCase, create_case_from_record
from src.llm.explanation_agent import ExplanationResult, generate_transaction_explanation
from src.llm.guardrails import check_llm_request_safety, refusal_message
from src.llm.investigation_agent import InvestigationResult, generate_investigation_summary
from src.llm.rag_retriever import LocalRAGRetriever, RetrievalResult, default_policy_retriever


class CopilotResponseType(str, Enum):
    POLICY_ANSWER = "POLICY_ANSWER"
    TRANSACTION_EXPLANATION = "TRANSACTION_EXPLANATION"
    CASE_INVESTIGATION = "CASE_INVESTIGATION"
    GUARDRAIL_REFUSAL = "GUARDRAIL_REFUSAL"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


@dataclass(frozen=True)
class CopilotResponse:
    allowed: bool
    response_type: CopilotResponseType
    answer: str
    retrieved_sources: List[str]
    guardrail_categories: List[str]
    confidence_note: str
    structured_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["response_type"] = self.response_type.value
        return data


def _sources_from_results(results: List[RetrievalResult]) -> List[str]:
    seen = set()
    sources: List[str] = []

    for result in results:
        source = result.chunk.source_path
        if source not in seen:
            sources.append(source)
            seen.add(source)

    return sources


def _format_policy_context(results: List[RetrievalResult]) -> str:
    if not results:
        return ""

    sections: List[str] = []

    for result in results:
        source_name = Path(result.chunk.source_path).name
        sections.append(
            f"Source: {source_name}\n"
            f"Relevance score: {result.score:.3f}\n"
            f"{result.chunk.text.strip()}"
        )

    return "\n\n---\n\n".join(sections)


def _summarize_policy_answer(question: str, results: List[RetrievalResult]) -> str:
    if not results:
        return (
            "I do not have enough retrieved FinShield policy context to answer that confidently. "
            "Ask a question related to risk policy, fraud investigation, audit requirements, "
            "model monitoring, calibration, or case handling."
        )

    context = _format_policy_context(results)

    return "\n".join(
        [
            "## FinShield Policy-Grounded Answer",
            "",
            f"Question: {question.strip()}",
            "",
            "### Retrieved Context",
            "",
            context,
            "",
            "### Answer",
            "",
            "Based on the retrieved FinShield policy context, the answer should be interpreted "
            "within the platform's advisory boundaries. The analyst assistant can explain "
            "risk policy, summarize evidence, and suggest review steps, but it cannot override "
            "ALLOW, REVIEW, or BLOCK decisions.",
            "",
            "### Safe Next Step",
            "",
            "Use the retrieved policy context to review the relevant transaction, preserve the "
            "audit trail, and document any analyst action taken.",
        ]
    )


def get_default_retriever() -> LocalRAGRetriever:
    return default_policy_retriever("docs")


def answer_policy_question(
    question: str,
    retriever: Optional[LocalRAGRetriever] = None,
    top_k: int = 3,
) -> CopilotResponse:
    safety = check_llm_request_safety(question)

    if not safety.allowed:
        return CopilotResponse(
            allowed=False,
            response_type=CopilotResponseType.GUARDRAIL_REFUSAL,
            answer=refusal_message(safety),
            retrieved_sources=[],
            guardrail_categories=safety.categories,
            confidence_note="Blocked by guardrails before retrieval.",
            structured_payload=safety.to_dict(),
        )

    active_retriever = retriever or get_default_retriever()
    results = active_retriever.query(question, top_k=top_k)

    if not results:
        return CopilotResponse(
            allowed=True,
            response_type=CopilotResponseType.INSUFFICIENT_CONTEXT,
            answer=_summarize_policy_answer(question, results),
            retrieved_sources=[],
            guardrail_categories=[],
            confidence_note="No relevant policy context retrieved.",
            structured_payload={"results": []},
        )

    return CopilotResponse(
        allowed=True,
        response_type=CopilotResponseType.POLICY_ANSWER,
        answer=_summarize_policy_answer(question, results),
        retrieved_sources=_sources_from_results(results),
        guardrail_categories=[],
        confidence_note="Answer is grounded in retrieved FinShield policy context.",
        structured_payload={"results": [result.to_dict() for result in results]},
    )


def explain_transaction(
    question: str,
    transaction_record: Mapping[str, Any],
    retriever: Optional[LocalRAGRetriever] = None,
    top_k: int = 3,
) -> CopilotResponse:
    active_retriever = retriever or get_default_retriever()

    result: ExplanationResult = generate_transaction_explanation(
        record=transaction_record,
        retriever=active_retriever,
        user_question=question,
        top_k=top_k,
    )

    if not result.allowed:
        return CopilotResponse(
            allowed=False,
            response_type=CopilotResponseType.GUARDRAIL_REFUSAL,
            answer=result.explanation,
            retrieved_sources=[],
            guardrail_categories=result.guardrail_categories,
            confidence_note="Blocked by guardrails before transaction explanation.",
            structured_payload=result.to_dict(),
        )

    return CopilotResponse(
        allowed=True,
        response_type=CopilotResponseType.TRANSACTION_EXPLANATION,
        answer=result.explanation,
        retrieved_sources=result.retrieved_sources,
        guardrail_categories=[],
        confidence_note="Explanation is grounded in transaction evidence and retrieved policy context.",
        structured_payload=result.to_dict(),
    )


def investigate_case(
    question: str,
    case_or_record: FraudCase | Mapping[str, Any],
    retriever: Optional[LocalRAGRetriever] = None,
    top_k: int = 3,
) -> CopilotResponse:
    active_retriever = retriever or get_default_retriever()

    result: InvestigationResult = generate_investigation_summary(
        case_or_record=case_or_record,
        retriever=active_retriever,
        analyst_question=question,
        top_k=top_k,
    )

    if not result.allowed:
        return CopilotResponse(
            allowed=False,
            response_type=CopilotResponseType.GUARDRAIL_REFUSAL,
            answer=result.summary,
            retrieved_sources=[],
            guardrail_categories=result.guardrail_categories,
            confidence_note="Blocked by guardrails before case investigation.",
            structured_payload=result.to_dict(),
        )

    return CopilotResponse(
        allowed=True,
        response_type=CopilotResponseType.CASE_INVESTIGATION,
        answer=result.summary,
        retrieved_sources=result.retrieved_sources,
        guardrail_categories=[],
        confidence_note="Investigation is grounded in case evidence and retrieved policy context.",
        structured_payload=result.to_dict(),
    )


def ask_finshield_copilot(
    question: str,
    transaction_record: Optional[Mapping[str, Any]] = None,
    case_record: Optional[FraudCase | Mapping[str, Any]] = None,
    retriever: Optional[LocalRAGRetriever] = None,
    top_k: int = 3,
) -> CopilotResponse:
    """
    Single safe entry point for the FinShield analyst copilot.

    Routing:
    - If case_record is supplied, run case investigation.
    - Else if transaction_record is supplied, run transaction explanation.
    - Else answer as a policy-grounded RAG question.
    """

    if case_record is not None:
        return investigate_case(
            question=question,
            case_or_record=case_record,
            retriever=retriever,
            top_k=top_k,
        )

    if transaction_record is not None:
        return explain_transaction(
            question=question,
            transaction_record=transaction_record,
            retriever=retriever,
            top_k=top_k,
        )

    return answer_policy_question(
        question=question,
        retriever=retriever,
        top_k=top_k,
    )


def create_case_and_investigate(
    question: str,
    transaction_record: Mapping[str, Any],
    retriever: Optional[LocalRAGRetriever] = None,
    top_k: int = 3,
) -> CopilotResponse:
    case = create_case_from_record(transaction_record)

    return investigate_case(
        question=question,
        case_or_record=case,
        retriever=retriever,
        top_k=top_k,
    )


def format_copilot_response_for_dashboard(response: CopilotResponse) -> Dict[str, Any]:
    return {
        "allowed": response.allowed,
        "response_type": response.response_type.value,
        "answer": response.answer,
        "retrieved_sources": response.retrieved_sources,
        "guardrail_categories": response.guardrail_categories,
        "confidence_note": response.confidence_note,
    }
