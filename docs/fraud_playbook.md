# FinShield Fraud Investigation Playbook

This playbook describes how analysts should interpret FinShield risk signals and investigate suspicious transactions.

## Investigation Goals

A fraud investigation should determine:

- What triggered the decision?
- Which evidence supports the decision?
- Is the activity consistent with user behavior?
- Does the event suggest account takeover?
- Should the transaction remain blocked, be reviewed further, or be cleared?
- What should be recorded in the audit trail?

## Common Risk Signals

| Signal | Meaning | Typical Action |
|---|---|---|
| High fraud probability | Supervised model predicts strong fraud risk | Review or block |
| Anomaly flag | Transaction differs from expected behavior | Review context |
| Velocity violation | Too many transactions in a short window | Step-up authentication |
| High transaction amount | Amount exceeds expected threshold | Review or block |
| New device | User appears from unseen device | Verify identity |
| Foreign IP | Location or network appears unusual | Verify session |
| Multiple failed logins | Possible credential attack | Escalate if combined with risk |
| Low model confidence | Model is uncertain | Review rather than blindly allow |

## Account Takeover Pattern

A possible account takeover pattern may include:

- New device
- Foreign IP or unusual region
- Multiple failed login attempts
- Sudden high-value transaction
- Anomaly flag
- High fraud probability

Recommended action:

1. Block or hold the transaction if risk is severe.
2. Verify user identity.
3. Review recent account activity.
4. Check for repeated login failures.
5. Escalate if multiple strong indicators are present.

## Review Workflow

For `REVIEW` decisions:

1. Inspect triggered rules.
2. Check model probability and confidence.
3. Check anomaly evidence.
4. Compare transaction behavior with normal account behavior.
5. Request step-up authentication if needed.
6. Add analyst note.
7. Resolve as genuine or suspicious.

## Block Workflow

For `BLOCK` decisions:

1. Keep the transaction blocked.
2. Preserve the full audit trail.
3. Create or update the investigation case.
4. Review account takeover indicators.
5. Escalate critical cases.
6. Require analyst approval before resolution.

## Analyst Note Guidelines

A strong analyst note should include:

- The final decision
- Key triggered evidence
- Risk score or probability
- Whether anomaly detection was involved
- Recommended action
- Any uncertainty or missing context

Example:

```text
Transaction TXN-1048 was blocked due to high fraud probability, anomaly detection, and suspicious account access indicators. Recommend user identity verification and review of recent account activity before allowing further transactions.
