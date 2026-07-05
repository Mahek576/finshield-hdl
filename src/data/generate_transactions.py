from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "sample_transactions.csv"


def create_account_profiles(rng, n_accounts=300):
    account_ids = [f"ACC_{i:04d}" for i in range(n_accounts)]

    profiles = pd.DataFrame({
        "account_id": account_ids,
        "account_age_days": rng.integers(30, 2500, size=n_accounts),
        "avg_amount_30d": rng.lognormal(mean=np.log(2500), sigma=0.7, size=n_accounts),
        "daily_limit": rng.choice(
            [50000, 100000, 200000, 500000],
            size=n_accounts,
            p=[0.35, 0.35, 0.2, 0.1]
        )
    })

    profiles["avg_amount_30d"] = profiles["avg_amount_30d"].round(2)

    return profiles


def generate_normal_transaction(rng, profile, timestamp, transaction_id):
    avg_amount = profile["avg_amount_30d"]
    amount = rng.lognormal(mean=np.log(max(avg_amount, 100)), sigma=0.45)

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp,
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.05, 0.45) * profile["daily_limit"]), 2),
        "daily_limit": float(profile["daily_limit"]),
        "tx_count_2min": int(rng.choice([1, 1, 1, 2, 2, 3])),
        "beneficiary_age_days": int(rng.integers(30, 1000)),
        "is_new_device": int(rng.random() < 0.03),
        "is_new_location": int(rng.random() < 0.04),
        "failed_login_count_1h": int(rng.choice([0, 0, 0, 1])),
        "hour_of_day": int(timestamp.hour),
        "merchant_risk_score": int(rng.integers(5, 45)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "NORMAL",
        "is_fraud": 0
    }


def generate_high_amount_transaction(rng, profile, timestamp, transaction_id):
    daily_limit = profile["daily_limit"]
    amount = rng.uniform(0.75, 1.4) * daily_limit

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp,
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.45, 0.95) * daily_limit), 2),
        "daily_limit": float(daily_limit),
        "tx_count_2min": int(rng.integers(1, 4)),
        "beneficiary_age_days": int(rng.integers(10, 400)),
        "is_new_device": int(rng.random() < 0.15),
        "is_new_location": int(rng.random() < 0.15),
        "failed_login_count_1h": int(rng.integers(0, 3)),
        "hour_of_day": int(timestamp.hour),
        "merchant_risk_score": int(rng.integers(35, 75)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "HIGH_AMOUNT_RISK",
        "is_fraud": 1
    }


def generate_velocity_spike_transaction(rng, profile, timestamp, transaction_id):
    avg_amount = profile["avg_amount_30d"]
    amount = rng.uniform(1.2, 3.5) * avg_amount

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp,
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.2, 0.7) * profile["daily_limit"]), 2),
        "daily_limit": float(profile["daily_limit"]),
        "tx_count_2min": int(rng.integers(5, 13)),
        "beneficiary_age_days": int(rng.integers(5, 500)),
        "is_new_device": int(rng.random() < 0.2),
        "is_new_location": int(rng.random() < 0.2),
        "failed_login_count_1h": int(rng.integers(0, 3)),
        "hour_of_day": int(timestamp.hour),
        "merchant_risk_score": int(rng.integers(30, 80)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "VELOCITY_SPIKE",
        "is_fraud": 1
    }


def generate_account_takeover_transaction(rng, profile, timestamp, transaction_id):
    avg_amount = profile["avg_amount_30d"]
    amount = rng.uniform(2.0, 7.0) * avg_amount

    suspicious_hour = int(rng.choice([0, 1, 2, 3, 4, 23]))

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp.replace(hour=suspicious_hour),
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.35, 0.85) * profile["daily_limit"]), 2),
        "daily_limit": float(profile["daily_limit"]),
        "tx_count_2min": int(rng.integers(3, 9)),
        "beneficiary_age_days": int(rng.integers(0, 7)),
        "is_new_device": 1,
        "is_new_location": 1,
        "failed_login_count_1h": int(rng.integers(3, 10)),
        "hour_of_day": suspicious_hour,
        "merchant_risk_score": int(rng.integers(55, 95)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "ACCOUNT_TAKEOVER",
        "is_fraud": 1
    }


def generate_risky_beneficiary_transaction(rng, profile, timestamp, transaction_id):
    avg_amount = profile["avg_amount_30d"]
    amount = rng.uniform(3.0, 8.0) * avg_amount

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp,
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.25, 0.8) * profile["daily_limit"]), 2),
        "daily_limit": float(profile["daily_limit"]),
        "tx_count_2min": int(rng.integers(1, 5)),
        "beneficiary_age_days": int(rng.integers(0, 3)),
        "is_new_device": int(rng.random() < 0.35),
        "is_new_location": int(rng.random() < 0.35),
        "failed_login_count_1h": int(rng.integers(0, 4)),
        "hour_of_day": int(timestamp.hour),
        "merchant_risk_score": int(rng.integers(60, 98)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "RISKY_BENEFICIARY",
        "is_fraud": 1
    }


def generate_mixed_risk_transaction(rng, profile, timestamp, transaction_id):
    avg_amount = profile["avg_amount_30d"]
    daily_limit = profile["daily_limit"]
    amount = max(rng.uniform(2.0, 5.0) * avg_amount, rng.uniform(0.25, 0.7) * daily_limit)

    return {
        "transaction_id": transaction_id,
        "account_id": profile["account_id"],
        "timestamp": timestamp,
        "amount": round(float(amount), 2),
        "daily_total_before_txn": round(float(rng.uniform(0.55, 0.95) * daily_limit), 2),
        "daily_limit": float(daily_limit),
        "tx_count_2min": int(rng.integers(4, 10)),
        "beneficiary_age_days": int(rng.integers(0, 10)),
        "is_new_device": int(rng.random() < 0.7),
        "is_new_location": int(rng.random() < 0.7),
        "failed_login_count_1h": int(rng.integers(2, 8)),
        "hour_of_day": int(timestamp.hour),
        "merchant_risk_score": int(rng.integers(65, 99)),
        "account_age_days": int(profile["account_age_days"]),
        "avg_amount_30d": float(profile["avg_amount_30d"]),
        "risk_type": "MIXED_RISK",
        "is_fraud": 1
    }


def generate_transactions(n_transactions=6000, seed=42):
    rng = np.random.default_rng(seed)
    profiles = create_account_profiles(rng)

    start_time = datetime(2026, 7, 1, 0, 0, 0)
    rows = []

    risk_generators = {
        "NORMAL": generate_normal_transaction,
        "HIGH_AMOUNT_RISK": generate_high_amount_transaction,
        "VELOCITY_SPIKE": generate_velocity_spike_transaction,
        "ACCOUNT_TAKEOVER": generate_account_takeover_transaction,
        "RISKY_BENEFICIARY": generate_risky_beneficiary_transaction,
        "MIXED_RISK": generate_mixed_risk_transaction
    }

    risk_distribution = {
        "NORMAL": 0.78,
        "HIGH_AMOUNT_RISK": 0.06,
        "VELOCITY_SPIKE": 0.05,
        "ACCOUNT_TAKEOVER": 0.04,
        "RISKY_BENEFICIARY": 0.04,
        "MIXED_RISK": 0.03
    }

    risk_types = list(risk_distribution.keys())
    probabilities = list(risk_distribution.values())

    for i in range(n_transactions):
        profile = profiles.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
        risk_type = rng.choice(risk_types, p=probabilities)

        minutes_offset = int(rng.integers(0, 24 * 60))
        seconds_offset = int(rng.integers(0, 60))
        timestamp = start_time + timedelta(minutes=minutes_offset, seconds=seconds_offset)

        transaction_id = f"TXN_{i:06d}"

        row = risk_generators[risk_type](rng, profile, timestamp, transaction_id)
        rows.append(row)

    df = pd.DataFrame(rows)

    df["total_after_txn"] = df["daily_total_before_txn"] + df["amount"]
    df["daily_limit_utilization"] = df["total_after_txn"] / df["daily_limit"]
    df["amount_to_avg_ratio"] = df["amount"] / df["avg_amount_30d"]

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["transaction_id"] = [f"TXN_{i:06d}" for i in range(len(df))]

    return df


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = generate_transactions()

    df.to_csv(OUTPUT_PATH, index=False)

    print("Synthetic transaction dataset generated successfully.")
    print(f"Output path: {OUTPUT_PATH}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print()
    print("Risk type distribution:")
    print(df["risk_type"].value_counts())
    print()
    print("Fraud label distribution:")
    print(df["is_fraud"].value_counts())
    print()
    print("Sample rows:")
    print(df.head(5))


if __name__ == "__main__":
    main()