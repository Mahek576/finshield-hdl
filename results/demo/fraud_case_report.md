# Fraud Investigation Case Report: CASE-58D59E670F

## Case Summary

- Transaction ID: `TXN-DEMO-001`
- User ID: `USER-DEMO-001`
- Final Decision: `BLOCK`
- Priority: `CRITICAL`
- Status: `OPEN`
- Risk Score: `0.940`
- Fraud Probability: `0.910`
- Model Confidence: `0.820`
- Anomaly Flag: `True`
- Created At: `2026-07-21T07:45:35+00:00`
- Updated At: `2026-07-21T07:45:35+00:00`

## Evidence

- [rule] Transaction velocity is higher than expected for the user. (severity: 55/100, source: velocity_violation)
- [account_takeover] Transaction or login context includes a foreign IP indicator. (severity: 50/100, source: foreign_ip)
- [account_takeover] Transaction was initiated from a new device. (severity: 35/100, source: new_device)
- [account_takeover] Combined signals suggest possible account takeover behavior. (severity: 90/100, source: account_takeover_pattern)
- [anomaly] Anomaly detector flagged this transaction as unusual. (severity: 65/100, source: anomaly_detector)
- [model_score] Fraud model probability is high at 0.910. (severity: 80/100, source: fraud_model)

## Recommended Action

Block the transaction, verify user identity, and review recent account activity for account takeover indicators.

## Analyst Note

No analyst note recorded.
