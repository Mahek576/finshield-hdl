from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

import pandas as pd


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED_FRAUD = "RESOLVED_FRAUD"
    RESOLVED_GENUINE = "RESOLVED_GENUINE"
    CLOSED = "CLOSED"


class CasePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class EvidenceItem:
    evidence_type: str
    description: str
    severity: int = 0
    source: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = max(0, min(100, int(self.severity)))
        return data


@dataclass
class FraudCase:
    case_id: str
    transaction_id: str
    user_id: str
    decision: CaseDecision
    priority: CasePriority
    status: CaseStatus
    risk_score: float
    fraud_probability: float
    anomaly_flag: bool
    model_confidence: float
    evidence: List[EvidenceItem] = field(default_factory=list)
    recommended_action: str = ""
    analyst_note: str = ""
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "decision": self.decision.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "risk_score": self.risk_score,
            "fraud_probability": self.fraud_probability,
            "anomaly_flag": self.anomaly_flag,
            "model_confidence": self.model_confidence,
            "evidence": [item.to_dict() for item in self.evidence],
            "recommended_action": self.recommended_action,
            "analyst_note": self.analyst_note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _safe_str(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _clip_probability(value: Any) -> float:
    return max(0.0, min(1.0, _safe_float(value, 0.0)))


def extract_evidence_from_record(record: Mapping[str, Any]) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []

    rule_map = {
        "amount_limit_violation": ("rule", "Transaction amount exceeded the configured risk threshold.", 60),
        "daily_limit_violation": ("rule", "User daily transaction activity exceeded the configured threshold.", 65),
        "velocity_violation": ("rule", "Transaction velocity is higher than expected for the user.", 55),
        "foreign_ip": ("account_takeover", "Transaction or login context includes a foreign IP indicator.", 50),
        "new_device": ("account_takeover", "Transaction was initiated from a new device.", 35),
        "multiple_failed_logins": ("account_takeover", "Multiple failed login attempts were observed.", 70),
        "account_takeover_pattern": ("account_takeover", "Combined signals suggest possible account takeover behavior.", 90),
        "blacklisted_merchant": ("rule", "Merchant appears in a high-risk or blocked merchant list.", 85),
        "high_risk_country": ("rule", "Transaction is associated with a high-risk country or region.", 70),
        "unusual_time": ("behavior", "Transaction occurred at an unusual time for the user.", 30),
    }

    for field_name, (evidence_type, description, severity) in rule_map.items():
        if _safe_bool(record.get(field_name, False)):
            evidence.append(
                EvidenceItem(
                    evidence_type=evidence_type,
                    description=description,
                    severity=severity,
                    source=field_name,
                )
            )

    anomaly_value = record.get(
        "anomaly_flag",
        record.get("is_anomaly", record.get("anomaly_detected", False)),
    )
    if _safe_bool(anomaly_value):
        evidence.append(
            EvidenceItem(
                evidence_type="anomaly",
                description="Anomaly detector flagged this transaction as unusual.",
                severity=65,
                source="anomaly_detector",
            )
        )

    confidence = _clip_probability(
        record.get(
            "model_confidence",
            record.get("ml_confidence", record.get("confidence_score", 1.0)),
        )
    )
    if confidence < 0.55:
        evidence.append(
            EvidenceItem(
                evidence_type="model_confidence",
                description=f"Model confidence is low at {confidence:.3f}.",
                severity=40,
                source="model_confidence",
            )
        )

    fraud_probability = _clip_probability(
        record.get(
            "fraud_probability",
            record.get("ml_fraud_probability", record.get("fraud_score", 0.0)),
        )
    )
    if fraud_probability >= 0.75:
        evidence.append(
            EvidenceItem(
                evidence_type="model_score",
                description=f"Fraud model probability is high at {fraud_probability:.3f}.",
                severity=80,
                source="fraud_model",
            )
        )
    elif fraud_probability >= 0.35:
        evidence.append(
            EvidenceItem(
                evidence_type="model_score",
                description=f"Fraud model probability is elevated at {fraud_probability:.3f}.",
                severity=45,
                source="fraud_model",
            )
        )

    return evidence


def infer_case_priority(
    decision: CaseDecision,
    risk_score: float,
    fraud_probability: float,
    anomaly_flag: bool,
    evidence: Optional[Iterable[EvidenceItem]] = None,
) -> CasePriority:
    evidence_items = list(evidence or [])
    max_evidence_severity = max((item.severity for item in evidence_items), default=0)

    if decision == CaseDecision.BLOCK and (
        risk_score >= 0.90 or fraud_probability >= 0.90 or max_evidence_severity >= 85
    ):
        return CasePriority.CRITICAL

    if decision == CaseDecision.BLOCK:
        return CasePriority.HIGH

    if decision == CaseDecision.REVIEW and (
        risk_score >= 0.65 or fraud_probability >= 0.65 or anomaly_flag
    ):
        return CasePriority.HIGH

    if decision == CaseDecision.REVIEW:
        return CasePriority.MEDIUM

    if anomaly_flag or max_evidence_severity >= 50:
        return CasePriority.MEDIUM

    return CasePriority.LOW


def recommend_action(
    decision: CaseDecision,
    priority: CasePriority,
    anomaly_flag: bool,
    evidence: Iterable[EvidenceItem],
) -> str:
    evidence_types = {item.evidence_type for item in evidence}

    if decision == CaseDecision.BLOCK:
        if "account_takeover" in evidence_types:
            return (
                "Block the transaction, verify user identity, and review recent "
                "account activity for account takeover indicators."
            )

        if priority == CasePriority.CRITICAL:
            return (
                "Block the transaction immediately, escalate to fraud operations, "
                "and require analyst approval before resolution."
            )

        return "Block the transaction and send it for fraud analyst review."

    if decision == CaseDecision.REVIEW:
        if anomaly_flag:
            return (
                "Route to step-up authentication and analyst review because anomaly "
                "signals indicate unusual behavior."
            )

        return "Route to step-up authentication or manual review before allowing the transaction."

    if anomaly_flag:
        return (
            "Allow with monitoring. Keep the transaction in the audit trail because "
            "an anomaly signal was observed."
        )

    return "Allow the transaction and retain the standard audit trace."


def create_case_from_record(record: Mapping[str, Any]) -> FraudCase:
    transaction_id = _safe_str(
        record.get("transaction_id", record.get("txn_id", record.get("id"))),
        default=f"TXN-{uuid4().hex[:8].upper()}",
    )

    user_id = _safe_str(
        record.get("user_id", record.get("customer_id", record.get("account_id"))),
        default="UNKNOWN_USER",
    )

    decision_text = _safe_str(
        record.get("final_decision", record.get("decision", record.get("final_action"))),
        default="REVIEW",
    ).upper()

    if decision_text not in {item.value for item in CaseDecision}:
        decision_text = "REVIEW"

    decision = CaseDecision(decision_text)

    fraud_probability = _clip_probability(
        record.get(
            "fraud_probability",
            record.get("ml_fraud_probability", record.get("fraud_score", 0.0)),
        )
    )

    risk_score = _clip_probability(
        record.get("risk_score", record.get("adjusted_risk_score", fraud_probability))
    )

    anomaly_flag = _safe_bool(
        record.get("anomaly_flag", record.get("is_anomaly", record.get("anomaly_detected", False)))
    )

    model_confidence = _clip_probability(
        record.get("model_confidence", record.get("ml_confidence", record.get("confidence_score", 1.0)))
    )

    evidence = extract_evidence_from_record(record)

    priority = infer_case_priority(
        decision=decision,
        risk_score=risk_score,
        fraud_probability=fraud_probability,
        anomaly_flag=anomaly_flag,
        evidence=evidence,
    )

    status = CaseStatus.OPEN if decision in {CaseDecision.REVIEW, CaseDecision.BLOCK} else CaseStatus.CLOSED

    action = recommend_action(
        decision=decision,
        priority=priority,
        anomaly_flag=anomaly_flag,
        evidence=evidence,
    )

    return FraudCase(
        case_id=f"CASE-{uuid4().hex[:10].upper()}",
        transaction_id=transaction_id,
        user_id=user_id,
        decision=decision,
        priority=priority,
        status=status,
        risk_score=risk_score,
        fraud_probability=fraud_probability,
        anomaly_flag=anomaly_flag,
        model_confidence=model_confidence,
        evidence=evidence,
        recommended_action=action,
        analyst_note=_safe_str(record.get("analyst_note"), default=""),
    )


def should_create_case(record: Mapping[str, Any]) -> bool:
    decision = _safe_str(
        record.get("final_decision", record.get("decision", record.get("final_action"))),
        default="",
    ).upper()

    if decision in {"REVIEW", "BLOCK"}:
        return True

    anomaly_flag = _safe_bool(
        record.get("anomaly_flag", record.get("is_anomaly", record.get("anomaly_detected", False)))
    )
    if anomaly_flag:
        return True

    risk_score = _clip_probability(record.get("risk_score", record.get("fraud_probability", 0.0)))
    return risk_score >= 0.35


def create_cases_from_records(records: Iterable[Mapping[str, Any]]) -> List[FraudCase]:
    return [create_case_from_record(record) for record in records if should_create_case(record)]


def update_case_status(
    case: FraudCase,
    status: CaseStatus,
    analyst_note: Optional[str] = None,
) -> FraudCase:
    case.status = status
    case.updated_at = _now_iso()

    if analyst_note is not None:
        case.analyst_note = analyst_note

    return case


def case_to_markdown(case: FraudCase) -> str:
    evidence_lines = []

    if case.evidence:
        for item in case.evidence:
            evidence_lines.append(
                f"- [{item.evidence_type}] {item.description} "
                f"(severity: {item.severity}/100, source: {item.source})"
            )
    else:
        evidence_lines.append("- No additional evidence items were recorded.")

    analyst_note = case.analyst_note.strip() if case.analyst_note else "No analyst note recorded."

    return "\n".join(
        [
            f"# Fraud Investigation Case Report: {case.case_id}",
            "",
            "## Case Summary",
            "",
            f"- Transaction ID: `{case.transaction_id}`",
            f"- User ID: `{case.user_id}`",
            f"- Final Decision: `{case.decision.value}`",
            f"- Priority: `{case.priority.value}`",
            f"- Status: `{case.status.value}`",
            f"- Risk Score: `{case.risk_score:.3f}`",
            f"- Fraud Probability: `{case.fraud_probability:.3f}`",
            f"- Model Confidence: `{case.model_confidence:.3f}`",
            f"- Anomaly Flag: `{case.anomaly_flag}`",
            f"- Created At: `{case.created_at}`",
            f"- Updated At: `{case.updated_at}`",
            "",
            "## Evidence",
            "",
            *evidence_lines,
            "",
            "## Recommended Action",
            "",
            case.recommended_action,
            "",
            "## Analyst Note",
            "",
            analyst_note,
            "",
        ]
    )


def cases_to_dataframe(cases: Iterable[FraudCase]) -> pd.DataFrame:
    rows = []

    for case in cases:
        data = case.to_dict()
        data["evidence_count"] = len(case.evidence)
        data["evidence_text"] = "; ".join(item.description for item in case.evidence)
        rows.append(data)

    return pd.DataFrame(rows)


def save_cases(
    cases: Iterable[FraudCase],
    output_dir: str | Path = "results",
    prefix: str = "fraud_cases",
) -> Dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    case_list = list(cases)
    generated_paths: Dict[str, Path] = {}

    csv_path = output_path / f"{prefix}.csv"
    cases_to_dataframe(case_list).to_csv(csv_path, index=False)
    generated_paths["cases_csv"] = csv_path

    reports_dir = output_path / f"{prefix}_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    for case in case_list:
        report_path = reports_dir / f"{case.case_id}.md"
        report_path.write_text(case_to_markdown(case), encoding="utf-8")

    generated_paths["reports_dir"] = reports_dir
    return generated_paths


def summarize_cases(cases: Iterable[FraudCase]) -> Dict[str, Any]:
    case_list = list(cases)

    if not case_list:
        return {
            "total_cases": 0,
            "by_status": {},
            "by_priority": {},
            "by_decision": {},
            "average_risk_score": 0.0,
            "average_fraud_probability": 0.0,
        }

    frame = cases_to_dataframe(case_list)

    return {
        "total_cases": int(len(case_list)),
        "by_status": frame["status"].value_counts().sort_index().to_dict(),
        "by_priority": frame["priority"].value_counts().sort_index().to_dict(),
        "by_decision": frame["decision"].value_counts().sort_index().to_dict(),
        "average_risk_score": float(frame["risk_score"].mean()),
        "average_fraud_probability": float(frame["fraud_probability"].mean()),
    }
