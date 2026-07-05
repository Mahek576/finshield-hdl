from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "rule_scored_transactions.csv"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "finshield_fraud_model.joblib"

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ml_scored_transactions.csv"
METRICS_PATH = PROJECT_ROOT / "results" / "model_metrics.json"
FEATURE_IMPORTANCE_PATH = PROJECT_ROOT / "results" / "feature_importance.csv"


FEATURE_COLUMNS = [
    "amount",
    "daily_total_before_txn",
    "daily_limit",
    "tx_count_2min",
    "beneficiary_age_days",
    "is_new_device",
    "is_new_location",
    "failed_login_count_1h",
    "hour_of_day",
    "merchant_risk_score",
    "account_age_days",
    "avg_amount_30d",
    "total_after_txn",
    "daily_limit_utilization",
    "amount_to_avg_ratio"
]

TARGET_COLUMN = "is_fraud"


def load_dataset():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Run src/rules/risk_rules.py before training the ML model."
        )

    df = pd.read_csv(INPUT_PATH)

    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]

    if missing_features:
        raise ValueError(f"Missing required feature columns: {missing_features}")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    return df


def prepare_features(df):
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)

    return X, y


def train_model(X_train, y_train):
    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    return model


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "average_precision": round(float(average_precision_score(y_test, y_prob)), 4),
        "confusion_matrix": {
            "true_negative": int(cm[0][0]),
            "false_positive": int(cm[0][1]),
            "false_negative": int(cm[1][0]),
            "true_positive": int(cm[1][1])
        },
        "classification_report": classification_report(
            y_test,
            y_pred,
            target_names=["normal", "fraud"],
            output_dict=True,
            zero_division=0
        )
    }

    return metrics


def add_ml_scores(df, model):
    scored_df = df.copy()

    X_all = scored_df[FEATURE_COLUMNS].copy()
    X_all = X_all.replace([np.inf, -np.inf], np.nan)
    X_all = X_all.fillna(0)

    fraud_probability = model.predict_proba(X_all)[:, 1]
    predicted_fraud = model.predict(X_all)

    confidence = np.maximum(fraud_probability, 1 - fraud_probability)

    scored_df["ml_fraud_probability"] = fraud_probability
    scored_df["ml_fraud_score"] = np.round(fraud_probability * 100).astype(int)
    scored_df["model_confidence"] = np.round(confidence * 100).astype(int)
    scored_df["predicted_fraud"] = predicted_fraud.astype(int)

    return scored_df


def save_feature_importance(model):
    feature_importance = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": model.feature_importances_
    })

    feature_importance = feature_importance.sort_values(
        "importance",
        ascending=False
    ).reset_index(drop=True)

    feature_importance.to_csv(FEATURE_IMPORTANCE_PATH, index=False)

    return feature_importance


def save_outputs(model, scored_df, metrics, feature_importance):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "feature_columns": FEATURE_COLUMNS
        },
        MODEL_PATH
    )

    scored_df.to_csv(OUTPUT_PATH, index=False)

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)


def main():
    df = load_dataset()
    X, y = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model = train_model(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)
    scored_df = add_ml_scores(df, model)
    feature_importance = save_feature_importance(model)

    save_outputs(model, scored_df, metrics, feature_importance)

    print("ML fraud model training completed successfully.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Model path: {MODEL_PATH}")
    print(f"Scored output path: {OUTPUT_PATH}")
    print(f"Metrics path: {METRICS_PATH}")
    print(f"Feature importance path: {FEATURE_IMPORTANCE_PATH}")
    print()
    print("Model metrics:")
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"Precision: {metrics['precision']}")
    print(f"Recall: {metrics['recall']}")
    print(f"F1 score: {metrics['f1_score']}")
    print(f"ROC AUC: {metrics['roc_auc']}")
    print(f"Average precision: {metrics['average_precision']}")
    print()
    print("Confusion matrix:")
    print(metrics["confusion_matrix"])
    print()
    print("Top feature importances:")
    print(feature_importance.head(10))
    print()
    print("ML score sample:")
    print(
        scored_df[
            [
                "transaction_id",
                "risk_type",
                "is_fraud",
                "ml_fraud_score",
                "model_confidence",
                "predicted_fraud",
                "rule_action"
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()