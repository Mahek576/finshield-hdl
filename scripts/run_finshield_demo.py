from __future__ import annotations

# Ensure project root is importable when this script is run directly.
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.cases.case_manager import (
    create_case_from_record,
    case_to_markdown,
)
from src.llm.copilot_service import (
    answer_policy_question,
    create_case_and_investigate,
    explain_transaction,
)
from src.llm.rag_retriever import default_policy_retriever


DEMO_OUTPUT_DIR = PROJECT_ROOT / "results" / "demo"


def build_demo_transaction() -> Dict[str, Any]:
    """
    Create a representative high-risk transaction for FinShield demo flow.

    This transaction intentionally includes multiple suspicious signals so the
    platform can demonstrate fraud scoring, case creation, investigation, and
    analyst-copilot explanation.
    """

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


def save_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def save_json_like_text(path: Path, payload: Dict[str, Any]) -> Path:
    lines = []

    for key, value in payload.items():
        lines.append(f"{key}: {value}")

    return save_text(path, "\n".join(lines) + "\n")


def run_demo(output_dir: Path = DEMO_OUTPUT_DIR) -> Dict[str, Path]:
    """
    Run a complete offline FinShield demo.

    Generated outputs:
    - demo transaction CSV
    - fraud case Markdown report
    - transaction explanation Markdown
    - investigation report Markdown
    - policy answer Markdown
    - demo summary text
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    transaction = build_demo_transaction()
    retriever = default_policy_retriever("docs")

    transaction_df = pd.DataFrame([transaction])
    transaction_path = output_dir / "demo_transaction.csv"
    transaction_df.to_csv(transaction_path, index=False)

    case = create_case_from_record(transaction)
    case_report = case_to_markdown(case)
    case_report_path = save_text(
        output_dir / "fraud_case_report.md",
        case_report,
    )

    explanation_response = explain_transaction(
        question="Why was this transaction blocked?",
        transaction_record=transaction,
        retriever=retriever,
    )
    explanation_path = save_text(
        output_dir / "transaction_explanation.md",
        explanation_response.answer,
    )

    investigation_response = create_case_and_investigate(
        question="Investigate this blocked account takeover case.",
        transaction_record=transaction,
        retriever=retriever,
    )
    investigation_path = save_text(
        output_dir / "investigation_report.md",
        investigation_response.answer,
    )

    policy_response = answer_policy_question(
        question="What does BLOCK mean according to FinShield policy?",
        retriever=retriever,
    )
    policy_answer_path = save_text(
        output_dir / "policy_answer.md",
        policy_response.answer,
    )

    summary_payload = {
        "demo_status": "completed",
        "transaction_id": transaction["transaction_id"],
        "user_id": transaction["user_id"],
        "final_decision": transaction["final_decision"],
        "fraud_probability": transaction["fraud_probability"],
        "risk_score": transaction["risk_score"],
        "case_id": case.case_id,
        "case_priority": case.priority.value,
        "case_status": case.status.value,
        "explanation_response_type": explanation_response.response_type.value,
        "investigation_response_type": investigation_response.response_type.value,
        "policy_response_type": policy_response.response_type.value,
    }
    summary_path = save_json_like_text(
        output_dir / "demo_summary.txt",
        summary_payload,
    )

    generated_paths = {
        "transaction_csv": transaction_path,
        "case_report": case_report_path,
        "transaction_explanation": explanation_path,
        "investigation_report": investigation_path,
        "policy_answer": policy_answer_path,
        "demo_summary": summary_path,
    }

    return generated_paths


def main() -> None:
    generated_paths = run_demo()

    print("FinShield demo completed successfully.")
    print("Generated files:")

    for label, path in generated_paths.items():
        print(f"- {label}: {path}")


if __name__ == "__main__":
    main()
