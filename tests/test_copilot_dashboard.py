import pandas as pd

from src.dashboard.copilot_tab import (
    build_copilot_card,
    create_sample_dashboard_record,
    dataframe_row_to_record,
    format_sources_for_display,
    run_copilot_query_for_dashboard,
    select_record_by_transaction_id,
)
from src.llm.copilot_service import CopilotResponse, CopilotResponseType
from src.llm.rag_retriever import LocalRAGRetriever


def build_test_retriever(tmp_path):
    policy = tmp_path / "risk_policy.md"
    policy.write_text(
        "BLOCK means high risk. REVIEW means analyst review. "
        "The analyst assistant cannot override decisions.",
        encoding="utf-8",
    )
    return LocalRAGRetriever.from_paths([policy])


def test_dataframe_row_to_record_normalizes_fields():
    row = {
        "txn_id": "TXN-401",
        "customer_id": "USER-401",
        "decision": "block",
        "ml_fraud_probability": "0.88",
        "adjusted_risk_score": "0.91",
        "ml_confidence": "0.80",
        "anomaly_detected": "true",
        "velocity_violation": 1,
    }

    record = dataframe_row_to_record(row)

    assert record["transaction_id"] == "TXN-401"
    assert record["user_id"] == "USER-401"
    assert record["final_decision"] == "BLOCK"
    assert record["fraud_probability"] == 0.88
    assert record["risk_score"] == 0.91
    assert record["anomaly_flag"] is True
    assert record["velocity_violation"] is True


def test_select_record_by_transaction_id_finds_row():
    frame = pd.DataFrame(
        [
            {"transaction_id": "T1", "user_id": "U1", "final_decision": "ALLOW"},
            {"transaction_id": "T2", "user_id": "U2", "final_decision": "BLOCK"},
        ]
    )

    record = select_record_by_transaction_id(frame, "T2")

    assert record is not None
    assert record["transaction_id"] == "T2"
    assert record["final_decision"] == "BLOCK"


def test_select_record_by_transaction_id_returns_none_for_missing():
    frame = pd.DataFrame([{"transaction_id": "T1", "final_decision": "ALLOW"}])

    record = select_record_by_transaction_id(frame, "missing")

    assert record is None


def test_build_copilot_card_from_response():
    response = CopilotResponse(
        allowed=True,
        response_type=CopilotResponseType.POLICY_ANSWER,
        answer="Policy answer",
        retrieved_sources=["docs/risk_policy.md"],
        guardrail_categories=[],
        confidence_note="Grounded response.",
        structured_payload=None,
    )

    card = build_copilot_card(response)

    assert card.allowed is True
    assert card.response_type == "POLICY_ANSWER"
    assert card.answer == "Policy answer"
    assert card.retrieved_sources == ["docs/risk_policy.md"]


def test_format_sources_for_display():
    text = format_sources_for_display(["docs/a.md", "docs/b.md"])

    assert "- docs/a.md" in text
    assert "- docs/b.md" in text


def test_format_sources_for_display_empty():
    text = format_sources_for_display([])

    assert text == "No retrieved sources."


def test_create_sample_dashboard_record_is_block_case():
    record = create_sample_dashboard_record()

    assert record["final_decision"] == "BLOCK"
    assert record["fraud_probability"] > 0.8
    assert record["anomaly_flag"] is True


def test_run_copilot_query_for_dashboard_policy_mode(tmp_path):
    retriever = build_test_retriever(tmp_path)

    card = run_copilot_query_for_dashboard(
        question="What does BLOCK mean?",
        retriever=retriever,
    )

    assert card.allowed is True
    assert card.response_type == "POLICY_ANSWER"
    assert "BLOCK" in card.answer


def test_run_copilot_query_for_dashboard_transaction_mode(tmp_path):
    retriever = build_test_retriever(tmp_path)

    card = run_copilot_query_for_dashboard(
        question="Why was this transaction blocked?",
        transaction_record=create_sample_dashboard_record(),
        retriever=retriever,
    )

    assert card.allowed is True
    assert card.response_type == "TRANSACTION_EXPLANATION"
    assert "Final Decision: `BLOCK`" in card.answer
