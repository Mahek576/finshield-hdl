from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

from src.llm.copilot_service import (
    CopilotResponse,
    ask_finshield_copilot,
    format_copilot_response_for_dashboard,
)
from src.llm.rag_retriever import LocalRAGRetriever, default_policy_retriever


@dataclass(frozen=True)
class DashboardCopilotCard:
    title: str
    response_type: str
    allowed: bool
    answer: str
    confidence_note: str
    retrieved_sources: List[str]
    guardrail_categories: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_COPILOT_QUESTIONS = [
    "What does BLOCK mean according to FinShield policy?",
    "What does REVIEW mean and what should an analyst do next?",
    "Why was this transaction blocked?",
    "Summarize the evidence for this case.",
    "What audit fields should be preserved?",
]


def _safe_str(value: Any, default: str = "") -> str:
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


def dataframe_row_to_record(row: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Convert a dashboard dataframe row into the normalized record shape expected
    by the FinShield copilot service.
    """

    return {
        "transaction_id": _safe_str(
            row.get("transaction_id", row.get("txn_id", row.get("id"))),
            default="UNKNOWN_TRANSACTION",
        ),
        "user_id": _safe_str(
            row.get("user_id", row.get("customer_id", row.get("account_id"))),
            default="UNKNOWN_USER",
        ),
        "final_decision": _safe_str(
            row.get("final_decision", row.get("decision", row.get("final_action"))),
            default="REVIEW",
        ).upper(),
        "fraud_probability": _safe_float(
            row.get("fraud_probability", row.get("ml_fraud_probability", row.get("fraud_score"))),
            default=0.0,
        ),
        "risk_score": _safe_float(
            row.get("risk_score", row.get("adjusted_risk_score", row.get("final_risk_score"))),
            default=0.0,
        ),
        "model_confidence": _safe_float(
            row.get("model_confidence", row.get("ml_confidence", row.get("confidence_score"))),
            default=1.0,
        ),
        "anomaly_flag": _safe_bool(
            row.get("anomaly_flag", row.get("is_anomaly", row.get("anomaly_detected", False)))
        ),
        "amount_limit_violation": _safe_bool(row.get("amount_limit_violation", False)),
        "daily_limit_violation": _safe_bool(row.get("daily_limit_violation", False)),
        "velocity_violation": _safe_bool(row.get("velocity_violation", False)),
        "foreign_ip": _safe_bool(row.get("foreign_ip", False)),
        "new_device": _safe_bool(row.get("new_device", False)),
        "multiple_failed_logins": _safe_bool(row.get("multiple_failed_logins", False)),
        "account_takeover_pattern": _safe_bool(row.get("account_takeover_pattern", False)),
        "blacklisted_merchant": _safe_bool(row.get("blacklisted_merchant", False)),
        "high_risk_country": _safe_bool(row.get("high_risk_country", False)),
        "unusual_time": _safe_bool(row.get("unusual_time", False)),
    }


def select_record_by_transaction_id(
    frame: pd.DataFrame,
    transaction_id: str,
) -> Optional[Dict[str, Any]]:
    if frame.empty:
        return None

    candidate_columns = ["transaction_id", "txn_id", "id"]

    for column in candidate_columns:
        if column in frame.columns:
            matches = frame[frame[column].astype(str) == str(transaction_id)]
            if not matches.empty:
                return dataframe_row_to_record(matches.iloc[0].to_dict())

    return None


def build_copilot_card(
    response: CopilotResponse,
    title: str = "FinShield Analyst Copilot",
) -> DashboardCopilotCard:
    payload = format_copilot_response_for_dashboard(response)

    return DashboardCopilotCard(
        title=title,
        response_type=str(payload["response_type"]),
        allowed=bool(payload["allowed"]),
        answer=str(payload["answer"]),
        confidence_note=str(payload["confidence_note"]),
        retrieved_sources=list(payload.get("retrieved_sources", [])),
        guardrail_categories=list(payload.get("guardrail_categories", [])),
    )


def format_sources_for_display(sources: List[str]) -> str:
    if not sources:
        return "No retrieved sources."

    return "\n".join(f"- {source}" for source in sources)


def run_copilot_query_for_dashboard(
    question: str,
    transaction_record: Optional[Mapping[str, Any]] = None,
    case_record: Optional[Mapping[str, Any]] = None,
    retriever: Optional[LocalRAGRetriever] = None,
) -> DashboardCopilotCard:
    active_retriever = retriever or default_policy_retriever("docs")

    response = ask_finshield_copilot(
        question=question,
        transaction_record=transaction_record,
        case_record=case_record,
        retriever=active_retriever,
    )

    return build_copilot_card(response)


def create_sample_dashboard_record() -> Dict[str, Any]:
    return {
        "transaction_id": "TXN-DEMO-001",
        "user_id": "USER-DEMO-001",
        "final_decision": "BLOCK",
        "fraud_probability": 0.91,
        "risk_score": 0.94,
        "model_confidence": 0.82,
        "anomaly_flag": True,
        "velocity_violation": True,
        "new_device": True,
        "foreign_ip": True,
        "account_takeover_pattern": True,
    }


def render_copilot_tab(
    transactions_df: Optional[pd.DataFrame] = None,
    retriever: Optional[LocalRAGRetriever] = None,
) -> None:
    """
    Render the FinShield Analyst Copilot Streamlit tab.

    This function imports Streamlit lazily so unit tests can import this module
    without requiring a running Streamlit app.
    """

    import streamlit as st

    st.header("FinShield Analyst Copilot")
    st.caption(
        "Policy-grounded assistant for transaction explanation, case investigation, "
        "and risk-policy questions. Advisory only."
    )

    active_retriever = retriever or default_policy_retriever("docs")

    mode = st.radio(
        "Copilot mode",
        ["Policy question", "Explain transaction"],
        horizontal=True,
    )

    question = st.text_area(
        "Ask the copilot",
        value=DEFAULT_COPILOT_QUESTIONS[0],
        height=100,
    )

    selected_record: Optional[Dict[str, Any]] = None

    if mode == "Explain transaction":
        if transactions_df is not None and not transactions_df.empty:
            candidate_columns = [
                column
                for column in ["transaction_id", "txn_id", "id"]
                if column in transactions_df.columns
            ]

            if candidate_columns:
                id_column = candidate_columns[0]
                options = transactions_df[id_column].astype(str).tolist()
                selected_id = st.selectbox("Select transaction", options)
                selected_record = select_record_by_transaction_id(transactions_df, selected_id)
            else:
                st.warning("No transaction identifier column found. Using demo record.")
                selected_record = create_sample_dashboard_record()
        else:
            st.info("No transaction dataframe supplied. Using demo record.")
            selected_record = create_sample_dashboard_record()

        with st.expander("Selected transaction record", expanded=False):
            st.json(selected_record)

    if st.button("Run Copilot"):
        response = ask_finshield_copilot(
            question=question,
            transaction_record=selected_record if mode == "Explain transaction" else None,
            retriever=active_retriever,
        )

        card = build_copilot_card(response)

        if card.allowed:
            st.success(card.response_type)
        else:
            st.error(card.response_type)

        st.markdown(card.answer)

        with st.expander("Retrieved sources", expanded=False):
            st.markdown(format_sources_for_display(card.retrieved_sources))

        with st.expander("Guardrail categories", expanded=False):
            st.write(card.guardrail_categories or "No guardrail issues detected.")

        st.caption(card.confidence_note)
