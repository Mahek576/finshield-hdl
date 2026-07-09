from pathlib import Path
import json
import time
import warnings

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler


warnings.filterwarnings("ignore")


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "rule_scored_transactions.csv"

MODEL_COMPARISON_CSV = PROJECT_ROOT / "results" / "model_comparison.csv"
MODEL_COMPARISON_JSON = PROJECT_ROOT / "results" / "model_comparison.json"
BEST_MODEL_SUMMARY_PATH = PROJECT_ROOT / "results" / "best_model_summary.json"
BENCHMARK_SCORED_OUTPUT = PROJECT_ROOT / "data" / "processed" / "benchmark_scored_transactions.csv"


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
            "Run python src/rules/risk_rules.py before benchmarking models."
        )

    df = pd.read_csv(INPUT_PATH)

    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]

    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    return df


def prepare_features(df):
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(0)

    return X, y


def safe_roc_auc(y_true, y_score):
    try:
        return float(roc_auc_score(y_true, y_score))
    except ValueError:
        return None


def safe_average_precision(y_true, y_score):
    try:
        return float(average_precision_score(y_true, y_score))
    except ValueError:
        return None


def compute_metrics(model_name, model_type, y_true, y_pred, y_score, latency_ms_per_txn):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    tn = int(cm[0][0])
    fp = int(cm[0][1])
    fn = int(cm[1][0])
    tp = int(cm[1][1])

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = safe_roc_auc(y_true, y_score)
    pr_auc = safe_average_precision(y_true, y_score)

    selection_score = (
        0.45 * (pr_auc if pr_auc is not None else 0)
        + 0.30 * recall
        + 0.20 * f1
        + 0.05 * precision
    )

    return {
        "model_name": model_name,
        "model_type": model_type,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4) if roc_auc is not None else None,
        "average_precision": round(float(pr_auc), 4) if pr_auc is not None else None,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "true_positive": tp,
        "latency_ms_per_transaction": round(float(latency_ms_per_txn), 6),
        "selection_score": round(float(selection_score), 4)
    }


def measure_latency(score_function, X, repeats=5):
    score_function(X)

    start = time.perf_counter()

    for _ in range(repeats):
        score_function(X)

    end = time.perf_counter()

    average_batch_time = (end - start) / repeats
    latency_ms_per_txn = (average_batch_time / len(X)) * 1000

    return latency_ms_per_txn


def build_supervised_models():
    models = {
        "Logistic Regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=42
                    )
                )
            ]
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=250,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "Gradient Boosting": HistGradientBoostingClassifier(
            max_iter=250,
            learning_rate=0.06,
            max_leaf_nodes=31,
            class_weight="balanced",
            random_state=42
        ),
        "MLP Neural Network": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32, 16),
                        activation="relu",
                        solver="adam",
                        alpha=0.0005,
                        learning_rate_init=0.001,
                        max_iter=500,
                        early_stopping=True,
                        random_state=42
                    )
                )
            ]
        )
    }

    return models


def normalize_scores(train_scores, test_scores):
    train_scores = np.asarray(train_scores).reshape(-1, 1)
    test_scores = np.asarray(test_scores).reshape(-1, 1)

    scaler = MinMaxScaler()
    scaler.fit(train_scores)

    normalized_scores = scaler.transform(test_scores).ravel()
    normalized_scores = np.clip(normalized_scores, 0, 1)

    return normalized_scores


def train_and_evaluate_supervised_models(X_train, X_test, y_train, y_test, X_all):
    results = []
    all_scores = {}

    supervised_models = build_supervised_models()

    for model_name, model in supervised_models.items():
        print(f"Training {model_name}...")

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_score = model.predict_proba(X_test)[:, 1]

        latency = measure_latency(
            lambda data: model.predict_proba(data)[:, 1],
            X_test
        )

        metrics = compute_metrics(
            model_name=model_name,
            model_type="supervised_classifier",
            y_true=y_test,
            y_pred=y_pred,
            y_score=y_score,
            latency_ms_per_txn=latency
        )

        results.append(metrics)

        all_scores[model_name] = {
            "model": model,
            "all_score": model.predict_proba(X_all)[:, 1]
        }

    return results, all_scores


def train_and_evaluate_isolation_forest(X_train, X_test, y_train, y_test, X_all):
    print("Training Isolation Forest...")

    normal_train = X_train[y_train == 0]

    scaler = StandardScaler()
    normal_train_scaled = scaler.fit_transform(normal_train)
    X_test_scaled = scaler.transform(X_test)
    X_all_scaled = scaler.transform(X_all)

    model = IsolationForest(
        n_estimators=250,
        contamination=0.08,
        random_state=42,
        n_jobs=-1
    )

    model.fit(normal_train_scaled)

    train_anomaly_scores = -model.decision_function(normal_train_scaled)
    test_anomaly_scores = -model.decision_function(X_test_scaled)
    all_anomaly_scores = -model.decision_function(X_all_scaled)

    threshold = np.quantile(train_anomaly_scores, 0.95)

    y_pred = (test_anomaly_scores >= threshold).astype(int)
    y_score = normalize_scores(train_anomaly_scores, test_anomaly_scores)
    all_score = normalize_scores(train_anomaly_scores, all_anomaly_scores)

    latency = measure_latency(
        lambda data: -model.decision_function(scaler.transform(data)),
        X_test
    )

    metrics = compute_metrics(
        model_name="Isolation Forest",
        model_type="unsupervised_anomaly_detector",
        y_true=y_test,
        y_pred=y_pred,
        y_score=y_score,
        latency_ms_per_txn=latency
    )

    return metrics, all_score


def train_and_evaluate_autoencoder(X_train, X_test, y_train, y_test, X_all):
    print("Training Autoencoder Anomaly Detector...")

    normal_train = X_train[y_train == 0]

    scaler = StandardScaler()
    normal_train_scaled = scaler.fit_transform(normal_train)
    X_test_scaled = scaler.transform(X_test)
    X_all_scaled = scaler.transform(X_all)

    autoencoder = MLPRegressor(
        hidden_layer_sizes=(12, 6, 12),
        activation="relu",
        solver="adam",
        alpha=0.0005,
        learning_rate_init=0.001,
        max_iter=800,
        early_stopping=True,
        random_state=42
    )

    autoencoder.fit(normal_train_scaled, normal_train_scaled)

    normal_reconstruction = autoencoder.predict(normal_train_scaled)
    test_reconstruction = autoencoder.predict(X_test_scaled)
    all_reconstruction = autoencoder.predict(X_all_scaled)

    train_errors = np.mean((normal_train_scaled - normal_reconstruction) ** 2, axis=1)
    test_errors = np.mean((X_test_scaled - test_reconstruction) ** 2, axis=1)
    all_errors = np.mean((X_all_scaled - all_reconstruction) ** 2, axis=1)

    threshold = np.quantile(train_errors, 0.95)

    y_pred = (test_errors >= threshold).astype(int)
    y_score = normalize_scores(train_errors, test_errors)
    all_score = normalize_scores(train_errors, all_errors)

    def score_function(data):
        data_scaled = scaler.transform(data)
        reconstructed = autoencoder.predict(data_scaled)
        errors = np.mean((data_scaled - reconstructed) ** 2, axis=1)
        return errors

    latency = measure_latency(score_function, X_test)

    metrics = compute_metrics(
        model_name="Autoencoder Anomaly Detector",
        model_type="neural_anomaly_detector",
        y_true=y_test,
        y_pred=y_pred,
        y_score=y_score,
        latency_ms_per_txn=latency
    )

    return metrics, all_score, all_errors


def slugify_model_name(model_name):
    return (
        model_name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def build_scored_output(df, model_scores, isolation_score, autoencoder_score, autoencoder_error):
    scored_df = df.copy()

    for model_name, info in model_scores.items():
        slug = slugify_model_name(model_name)
        scored_df[f"{slug}_score"] = np.round(info["all_score"] * 100).astype(int)

    scored_df["isolation_forest_anomaly_score"] = np.round(isolation_score * 100).astype(int)
    scored_df["autoencoder_anomaly_score"] = np.round(autoencoder_score * 100).astype(int)
    scored_df["autoencoder_reconstruction_error"] = autoencoder_error

    return scored_df


def save_outputs(results, scored_df):
    MODEL_COMPARISON_CSV.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_SCORED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    comparison_df = pd.DataFrame(results)

    comparison_df = comparison_df.sort_values(
        ["selection_score", "average_precision", "recall", "f1_score"],
        ascending=False
    ).reset_index(drop=True)

    best_model = comparison_df.iloc[0].to_dict()

    best_model_summary = {
        "best_model_name": best_model["model_name"],
        "best_model_type": best_model["model_type"],
        "selection_score": best_model["selection_score"],
        "reason": (
            "Best model selected using a weighted score prioritizing "
            "average precision, recall, F1 score, and precision."
        ),
        "metrics": best_model
    }

    comparison_df.to_csv(MODEL_COMPARISON_CSV, index=False)

    with open(MODEL_COMPARISON_JSON, "w", encoding="utf-8") as f:
        json.dump(comparison_df.to_dict(orient="records"), f, indent=4)

    with open(BEST_MODEL_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(best_model_summary, f, indent=4)

    scored_df.to_csv(BENCHMARK_SCORED_OUTPUT, index=False)

    return comparison_df, best_model_summary


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

    supervised_results, supervised_scores = train_and_evaluate_supervised_models(
        X_train,
        X_test,
        y_train,
        y_test,
        X
    )

    isolation_metrics, isolation_score = train_and_evaluate_isolation_forest(
        X_train,
        X_test,
        y_train,
        y_test,
        X
    )

    autoencoder_metrics, autoencoder_score, autoencoder_error = train_and_evaluate_autoencoder(
        X_train,
        X_test,
        y_train,
        y_test,
        X
    )

    all_results = supervised_results + [
        isolation_metrics,
        autoencoder_metrics
    ]

    scored_df = build_scored_output(
        df=df,
        model_scores=supervised_scores,
        isolation_score=isolation_score,
        autoencoder_score=autoencoder_score,
        autoencoder_error=autoencoder_error
    )

    comparison_df, best_model_summary = save_outputs(all_results, scored_df)

    print()
    print("Model benchmarking completed successfully.")
    print(f"Input path: {INPUT_PATH}")
    print(f"Model comparison CSV: {MODEL_COMPARISON_CSV}")
    print(f"Model comparison JSON: {MODEL_COMPARISON_JSON}")
    print(f"Best model summary: {BEST_MODEL_SUMMARY_PATH}")
    print(f"Benchmark scored output: {BENCHMARK_SCORED_OUTPUT}")
    print()
    print("Model comparison:")
    print(
        comparison_df[
            [
                "model_name",
                "model_type",
                "precision",
                "recall",
                "f1_score",
                "roc_auc",
                "average_precision",
                "false_positive",
                "false_negative",
                "latency_ms_per_transaction",
                "selection_score"
            ]
        ]
    )
    print()
    print("Best model:")
    print(json.dumps(best_model_summary, indent=4))


if __name__ == "__main__":
    main()