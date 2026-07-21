# FinShield Model Card

## Model Overview

FinShield is an AI-powered fintech fraud and risk intelligence platform.

The system combines:

- Supervised fraud detection
- Anomaly detection
- Cybersecurity rule checks
- Cost-sensitive decisioning
- Probability calibration
- Model monitoring
- Audit logging
- Case management
- Policy-grounded analyst copilot

The model layer is not used alone. It is part of a larger risk decisioning pipeline that converts fraud probability, anomaly evidence, rule signals, and confidence into operational decisions.

## Intended Use

FinShield is intended for:

- Demonstrating transaction fraud detection workflows
- Explaining fraud-risk decisions
- Comparing supervised and anomaly-based detection methods
- Generating audit-friendly decision traces
- Supporting fraud analyst investigation workflows
- Demonstrating production-aware AI/ML engineering practices

## Not Intended Use

FinShield is not intended for:

- Real banking deployment without validation
- Live financial decisioning
- Replacing human fraud analysts
- Making legally binding financial decisions
- Processing real customer data without privacy, security, and compliance controls

## Input Data

FinShield works with synthetic transaction data and engineered risk signals.

Example input categories include:

- Transaction amount
- Transaction frequency
- User/account behavior
- Merchant/category indicators
- Login/session risk signals
- Rule flags
- Model confidence
- Anomaly indicators

## Output

FinShield produces:

| Output | Meaning |
|---|---|
| Fraud probability | Estimated supervised fraud risk |
| Anomaly flag | Whether behavior appears unusual |
| Rule severity | Deterministic risk severity |
| Adjusted risk score | Risk after policy-based adjustments |
| Final decision | `ALLOW`, `REVIEW`, or `BLOCK` |
| Audit trace | Explanation and evidence behind decision |
| Case report | Investigation-ready case summary |

## Decision Levels

| Decision | Meaning |
|---|---|
| `ALLOW` | Transaction appears safe enough to proceed |
| `REVIEW` | Transaction requires step-up authentication or analyst review |
| `BLOCK` | Transaction risk is high enough to stop immediately |

## Models and Techniques

FinShield includes or supports:

- Random Forest fraud model
- Gradient Boosting model selection
- MLP benchmark
- Isolation Forest anomaly detection
- Autoencoder anomaly detection
- Probability calibration
- Cost-sensitive risk decisioning
- Drift monitoring

## Evaluation Dimensions

FinShield should be evaluated across:

| Dimension | Purpose |
|---|---|
| Accuracy | Overall classification correctness |
| Precision | How reliable fraud predictions are |
| Recall | How many fraud cases are detected |
| F1-score | Balance between precision and recall |
| ROC-AUC | Ranking quality |
| Average Precision | Useful for imbalanced fraud settings |
| Brier Score | Probability calibration quality |
| Log Loss | Penalizes confident wrong probabilities |
| Drift Metrics | Tracks feature and decision distribution changes |

## Explainability

FinShield supports explanation through:

- Rule trigger summaries
- Fraud probability reporting
- Adjusted risk score reporting
- Anomaly flag reporting
- Model confidence reporting
- Audit logs
- Case reports
- Policy-grounded analyst copilot

The analyst copilot is advisory only. It explains and investigates existing decisions but does not override them.

## Monitoring

FinShield includes monitoring for:

- Numeric feature drift
- Categorical feature drift
- Decision distribution drift
- Risk score shifts
- Review/block rate changes
- Monitoring alert levels: `OK`, `WARN`, `ALERT`

## Limitations

FinShield uses synthetic data, so real-world performance cannot be assumed.

Important limitations:

- Synthetic data may not represent real fraud patterns.
- Real-world fraud is adversarial and changes over time.
- Model thresholds require business validation.
- False positives and false negatives have different operational costs.
- Analyst copilot outputs must remain advisory and grounded in retrieved context.
- Real deployment would require privacy, compliance, security, and human oversight.

## Ethical and Safety Considerations

FinShield should be used with:

- Human oversight
- Auditability
- Clear decision boundaries
- Model monitoring
- Bias and fairness review
- Data privacy protections
- Clear separation between model decisioning and analyst assistance

## Summary

FinShield is designed as a portfolio-grade AI/ML risk intelligence platform, not just a fraud classifier.

It demonstrates how fraud detection can be extended into a complete risk operations workflow:

```text
Transaction Data
        |
        v
Fraud Model + Anomaly Detection + Rules
        |
        v
Cost-Sensitive Decisioning
        |
        v
Audit Trail + Case Management
        |
        v
Monitoring + Analyst Copilot
