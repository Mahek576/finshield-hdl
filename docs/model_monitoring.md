# Model Monitoring and Drift Detection

FinShield includes model monitoring utilities to detect whether transaction behavior, feature distributions, or final decision patterns have changed over time.

This matters because fraud systems are not static. Fraud patterns, customer behavior, transaction channels, merchant categories, and attacker strategies can shift after a model has been trained.

A strong fraud platform should therefore monitor not only model performance, but also the data and decision patterns flowing through the system.

## Monitoring Goals

FinShield monitoring helps answer:

- Are new transactions statistically different from the training/reference data?
- Are transaction amounts drifting upward or downward?
- Are risk scores becoming more concentrated in high-risk ranges?
- Are merchant or transaction categories changing?
- Are more transactions being reviewed or blocked than before?
- Is the model operating in a different environment than the one it was trained on?

## Drift Types

### Numeric Feature Drift

Numeric drift is measured using Population Stability Index.

Examples of numeric features:

- Transaction amount
- Risk score
- Fraud probability
- Model confidence
- User transaction count
- Transaction velocity

### Categorical Feature Drift

Categorical drift is measured using total variation distance.

Examples of categorical features:

- Merchant category
- Transaction channel
- Country or region
- Final decision
- Payment method

### Decision Distribution Drift

FinShield also monitors whether the distribution of final decisions has changed.

Example:

| Decision | Reference Batch | Current Batch |
|---|---:|---:|
| ALLOW | 85% | 62% |
| REVIEW | 10% | 25% |
| BLOCK | 5% | 13% |

A sharp increase in `REVIEW` or `BLOCK` may indicate fraud pattern changes, upstream data issues, or overly strict thresholds.

## Alert Levels

FinShield uses three monitoring levels:

| Level | Meaning |
|---|---|
| `OK` | No major drift detected |
| `WARN` | Moderate drift detected; review recommended |
| `ALERT` | Strong drift detected; investigation required |

## Generated Outputs

The monitoring module can write CSV reports such as:

```text
results/monitoring_numeric_drift.csv
results/monitoring_categorical_drift.csv
results/monitoring_decision_drift.csv
results/monitoring_summary.csv
