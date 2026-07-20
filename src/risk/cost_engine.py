from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional


class RiskDecision(str, Enum):
    """Final transaction decision used across FinShield."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class CostPolicy:
    """
    Business-aware policy for converting model/rule/anomaly evidence into
    ALLOW, REVIEW, or BLOCK decisions.

    Fraud decisioning is cost-sensitive:
    - False negatives are costly because fraud passes through.
    - False positives are costly because genuine users face friction.
    - REVIEW is a middle path that reduces risk but increases analyst workload.
    """

    review_threshold: float = 0.35
    block_threshold: float = 0.75

    anomaly_review_boost: float = 0.10
    anomaly_block_boost: float = 0.15

    low_confidence_threshold: float = 0.55
    low_confidence_review_boost: float = 0.08

    severe_rule_block_score: int = 80
    medium_rule_review_score: int = 40

    false_positive_cost: float = 1.0
    false_negative_cost: float = 8.0
    review_cost: float = 0.75


@dataclass(frozen=True)
class RiskDecisionResult:
    """Audit-friendly result returned by the cost-sensitive risk engine."""

    decision: RiskDecision
    raw_fraud_probability: float
    adjusted_risk_score: float
    rule_severity_score: int
    anomaly_flag: bool
    model_confidence: float
    expected_allow_cost: float
    expected_review_cost: float
    expected_block_cost: float
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data


RULE_WEIGHTS: Dict[str, int] = {
    "amount_limit_violation": 35,
    "daily_limit_violation": 35,
    "velocity_violation": 25,
    "foreign_ip": 20,
    "new_device": 15,
    "multiple_failed_logins": 30,
    "account_takeover_pattern": 50,
    "blacklisted_merchant": 45,
    "high_risk_country": 35,
    "unusual_time": 15,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def compute_rule_severity(rule_flags: Optional[Mapping[str, Any]]) -> int:
    """
    Convert rule flags into a deterministic 0-100 severity score.

    Unknown rule names are ignored so this function remains stable even if
    upstream systems include additional fields.
    """

    if not rule_flags:
        return 0

    severity = 0

    for rule_name, weight in RULE_WEIGHTS.items():
        if bool(rule_flags.get(rule_name, False)):
            severity += weight

    return min(100, severity)


def make_cost_sensitive_decision(
    fraud_probability: Any,
    model_confidence: Any = 1.0,
    anomaly_flag: Any = False,
    rule_flags: Optional[Mapping[str, Any]] = None,
    policy: Optional[CostPolicy] = None,
) -> RiskDecisionResult:
    """
    Convert risk evidence into ALLOW / REVIEW / BLOCK.

    Inputs:
    - fraud_probability: supervised model probability or risk score in [0, 1]
    - model_confidence: confidence in the model output in [0, 1]
    - anomaly_flag: whether anomaly detection flagged unusual behavior
    - rule_flags: deterministic cybersecurity/risk rule outputs
    - policy: optional CostPolicy override

    The output is intentionally explainable and suitable for audit logs,
    dashboards, and future analyst-copilot summaries.
    """

    active_policy = policy or CostPolicy()

    raw_prob = _clip(_safe_float(fraud_probability, 0.0))
    confidence = _clip(_safe_float(model_confidence, 1.0))
    anomaly = bool(anomaly_flag)
    rule_severity = compute_rule_severity(rule_flags)

    adjusted_risk = raw_prob
    reasons: List[str] = [f"Base fraud probability: {raw_prob:.3f}"]

    if rule_severity >= active_policy.severe_rule_block_score:
        adjusted_risk = max(
            adjusted_risk + 0.25,
            active_policy.block_threshold,
        )
        reasons.append(f"Severe rule risk detected with severity score {rule_severity}/100")
        reasons.append("Severe rule risk forces a block-level decision")
    elif rule_severity >= active_policy.medium_rule_review_score:
        adjusted_risk += 0.12
        reasons.append(f"Moderate rule risk detected with severity score {rule_severity}/100")
    elif rule_severity > 0:
        adjusted_risk += 0.05
        reasons.append(f"Minor rule risk detected with severity score {rule_severity}/100")

    if anomaly:
        adjusted_risk += active_policy.anomaly_review_boost
        reasons.append("Anomaly detector flagged unusual transaction behavior")

        if raw_prob >= active_policy.review_threshold:
            adjusted_risk += active_policy.anomaly_block_boost
            reasons.append("Anomaly flag combined with elevated fraud probability")

    if confidence < active_policy.low_confidence_threshold:
        adjusted_risk += active_policy.low_confidence_review_boost
        reasons.append(f"Model confidence is low at {confidence:.3f}")

    adjusted_risk = _clip(adjusted_risk)

    expected_allow_cost = adjusted_risk * active_policy.false_negative_cost
    expected_block_cost = (1.0 - adjusted_risk) * active_policy.false_positive_cost
    expected_review_cost = active_policy.review_cost

    if adjusted_risk >= active_policy.block_threshold:
        decision = RiskDecision.BLOCK
        reasons.append(
            f"Adjusted risk {adjusted_risk:.3f} exceeds block threshold "
            f"{active_policy.block_threshold:.3f}"
        )
    elif adjusted_risk >= active_policy.review_threshold:
        decision = RiskDecision.REVIEW
        reasons.append(
            f"Adjusted risk {adjusted_risk:.3f} exceeds review threshold "
            f"{active_policy.review_threshold:.3f}"
        )
    else:
        decision = RiskDecision.ALLOW
        reasons.append(
            f"Adjusted risk {adjusted_risk:.3f} is below review threshold "
            f"{active_policy.review_threshold:.3f}"
        )

    return RiskDecisionResult(
        decision=decision,
        raw_fraud_probability=raw_prob,
        adjusted_risk_score=adjusted_risk,
        rule_severity_score=rule_severity,
        anomaly_flag=anomaly,
        model_confidence=confidence,
        expected_allow_cost=expected_allow_cost,
        expected_review_cost=expected_review_cost,
        expected_block_cost=expected_block_cost,
        reasons=reasons,
    )


def explain_decision(result: RiskDecisionResult) -> str:
    """Return a human-readable explanation for dashboards and audit trails."""

    lines = [
        f"Decision: {result.decision.value}",
        f"Raw fraud probability: {result.raw_fraud_probability:.3f}",
        f"Adjusted risk score: {result.adjusted_risk_score:.3f}",
        f"Rule severity score: {result.rule_severity_score}/100",
        f"Anomaly flag: {result.anomaly_flag}",
        f"Model confidence: {result.model_confidence:.3f}",
        "Reasons:",
    ]

    for reason in result.reasons:
        lines.append(f"- {reason}")

    return "\n".join(lines)


def decision_from_transaction_row(
    row: Mapping[str, Any],
    policy: Optional[CostPolicy] = None,
) -> RiskDecisionResult:
    """
    Convenience adapter for dataframe rows, dict records, audit records, or
    dashboard-selected transactions.

    It supports multiple common column names so it can integrate without forcing
    one exact schema immediately.
    """

    fraud_probability = (
        row.get("fraud_probability")
        if "fraud_probability" in row
        else row.get("ml_fraud_probability", row.get("risk_score", row.get("fraud_score", 0.0)))
    )

    model_confidence = row.get(
        "model_confidence",
        row.get("ml_confidence", row.get("confidence_score", 1.0)),
    )

    anomaly_flag = row.get(
        "anomaly_flag",
        row.get("is_anomaly", row.get("anomaly_detected", False)),
    )

    rule_flags = {
        "amount_limit_violation": row.get("amount_limit_violation", False),
        "daily_limit_violation": row.get("daily_limit_violation", False),
        "velocity_violation": row.get("velocity_violation", False),
        "foreign_ip": row.get("foreign_ip", False),
        "new_device": row.get("new_device", False),
        "multiple_failed_logins": row.get("multiple_failed_logins", False),
        "account_takeover_pattern": row.get("account_takeover_pattern", False),
        "blacklisted_merchant": row.get("blacklisted_merchant", False),
        "high_risk_country": row.get("high_risk_country", False),
        "unusual_time": row.get("unusual_time", False),
    }

    return make_cost_sensitive_decision(
        fraud_probability=fraud_probability,
        model_confidence=model_confidence,
        anomaly_flag=anomaly_flag,
        rule_flags=rule_flags,
        policy=policy,
    )
