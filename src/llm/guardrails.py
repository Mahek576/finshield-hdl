from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str
    categories: List[str]
    safe_alternative: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


DISALLOWED_PATTERNS: Dict[str, List[str]] = {
    "decision_override": [
        "approve this blocked transaction",
        "approve blocked transaction",
        "override the decision",
        "reverse the block",
        "change block to allow",
        "change review to allow",
        "mark this as allow",
        "force allow",
        "bypass review",
    ],
    "policy_bypass": [
        "ignore policy",
        "ignore the policy",
        "ignore retrieved context",
        "do not follow policy",
        "forget the rules",
        "skip audit",
        "hide evidence",
        "delete audit",
        "remove audit",
    ],
    "prompt_extraction": [
        "show system prompt",
        "reveal system prompt",
        "show hidden instructions",
        "reveal hidden instructions",
        "print developer message",
        "ignore previous instructions",
    ],
    "unsupported_authority": [
        "you are the final fraud authority",
        "make the final fraud decision",
        "decide without evidence",
        "guarantee this is fraud",
        "guarantee this is genuine",
    ],
}


def normalize_request(text: str) -> str:
    return " ".join(str(text).lower().strip().split())


def check_llm_request_safety(user_request: str) -> GuardrailResult:
    normalized = normalize_request(user_request)

    if not normalized:
        return GuardrailResult(
            allowed=False,
            reason="Empty request cannot be processed safely.",
            categories=["empty_request"],
            safe_alternative="Ask a policy, case, or decision-explanation question.",
        )

    matched_categories: List[str] = []

    for category, patterns in DISALLOWED_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            matched_categories.append(category)

    if matched_categories:
        return GuardrailResult(
            allowed=False,
            reason="The request attempts to bypass FinShield decision, policy, or safety boundaries.",
            categories=matched_categories,
            safe_alternative=(
                "I can explain the decision evidence, summarize policy context, "
                "or generate an analyst review note instead."
            ),
        )

    return GuardrailResult(
        allowed=True,
        reason="Request is within advisory analyst-assistant boundaries.",
        categories=[],
        safe_alternative=None,
    )


def build_guarded_analyst_prompt(
    user_question: str,
    retrieved_context: str,
    case_context: Optional[str] = None,
) -> str:
    safety = check_llm_request_safety(user_question)

    if not safety.allowed:
        return (
            "The analyst request was blocked by FinShield guardrails.\n\n"
            f"Reason: {safety.reason}\n"
            f"Categories: {', '.join(safety.categories)}\n"
            f"Safe alternative: {safety.safe_alternative}"
        )

    case_section = case_context.strip() if case_context else "No case-specific context was provided."
    retrieved_section = retrieved_context.strip() if retrieved_context else "No retrieved policy context was available."

    return "\n".join(
        [
            "You are FinShield's policy-grounded analyst assistant.",
            "",
            "Operating rules:",
            "- You are advisory only.",
            "- You cannot approve, block, reverse, or override transaction decisions.",
            "- You cannot delete or alter audit evidence.",
            "- Use only retrieved policy context and provided case evidence.",
            "- If evidence is insufficient, say so clearly.",
            "- Distinguish recorded evidence from generated interpretation.",
            "",
            "Retrieved policy context:",
            retrieved_section,
            "",
            "Case context:",
            case_section,
            "",
            "Analyst question:",
            user_question.strip(),
            "",
            "Response requirements:",
            "- Give a concise, evidence-grounded answer.",
            "- Mention the relevant policy basis when available.",
            "- Do not invent missing facts.",
            "- End with a safe next-step recommendation when appropriate.",
        ]
    )


def refusal_message(result: GuardrailResult) -> str:
    if result.allowed:
        return ""

    return (
        f"I cannot help with that request because it violates FinShield guardrails: "
        f"{result.reason} "
        f"{result.safe_alternative or 'Ask for an explanation or policy-grounded review instead.'}"
    )
