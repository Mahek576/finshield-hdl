from pathlib import Path
import json
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FINAL_DECISIONS_PATH = PROJECT_ROOT / "data" / "processed" / "final_decision_transactions.csv"
AUDIT_VIEW_PATH = PROJECT_ROOT / "data" / "processed" / "audit_log_view.csv"
HARDWARE_PACKET_PATH = PROJECT_ROOT / "data" / "processed" / "hardware_risk_packets.csv"

MODEL_METRICS_PATH = PROJECT_ROOT / "results" / "model_metrics.json"
FEATURE_IMPORTANCE_PATH = PROJECT_ROOT / "results" / "feature_importance.csv"
AUDIT_SUMMARY_PATH = PROJECT_ROOT / "results" / "audit_summary.json"

MODEL_COMPARISON_PATH = PROJECT_ROOT / "results" / "model_comparison.csv"
BEST_MODEL_SUMMARY_PATH = PROJECT_ROOT / "results" / "best_model_summary.json"


st.set_page_config(
    page_title="FinShield HDL Dashboard",
    page_icon="🛡️",
    layout="wide"
)


def load_json(path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_data():
    required_files = [
        FINAL_DECISIONS_PATH,
        AUDIT_VIEW_PATH,
        HARDWARE_PACKET_PATH,
        MODEL_METRICS_PATH,
        FEATURE_IMPORTANCE_PATH,
        AUDIT_SUMMARY_PATH,
        MODEL_COMPARISON_PATH,
        BEST_MODEL_SUMMARY_PATH
    ]

    missing_files = [str(path) for path in required_files if not path.exists()]

    if missing_files:
        raise FileNotFoundError(
            "Missing required files. Run the full pipeline first:\n\n"
            "python run_pipeline.py\n\n"
            f"Missing files: {missing_files}"
        )

    final_df = pd.read_csv(FINAL_DECISIONS_PATH)
    audit_df = pd.read_csv(AUDIT_VIEW_PATH)
    hardware_df = pd.read_csv(HARDWARE_PACKET_PATH)
    feature_importance_df = pd.read_csv(FEATURE_IMPORTANCE_PATH)
    model_comparison_df = pd.read_csv(MODEL_COMPARISON_PATH)

    model_metrics = load_json(MODEL_METRICS_PATH)
    audit_summary = load_json(AUDIT_SUMMARY_PATH)
    best_model_summary = load_json(BEST_MODEL_SUMMARY_PATH)

    final_df["timestamp"] = pd.to_datetime(final_df["timestamp"])
    audit_df["timestamp"] = pd.to_datetime(audit_df["timestamp"])

    audit_lookup = audit_df[
        [
            "transaction_id",
            "severity",
            "decision_source"
        ]
    ].drop_duplicates("transaction_id")

    merged_df = final_df.merge(
        audit_lookup,
        on="transaction_id",
        how="left"
    )

    return (
        merged_df,
        audit_df,
        hardware_df,
        feature_importance_df,
        model_comparison_df,
        model_metrics,
        audit_summary,
        best_model_summary
    )


def metric_card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)


def format_percentage(value):
    return f"{round(value * 100, 2)}%"


def safe_columns(df, columns):
    return [column for column in columns if column in df.columns]


def main():
    st.title("🛡️ FinShield HDL")

    st.caption(
        "AI-powered fintech risk engine with supervised ML, anomaly detection, "
        "cybersecurity rules, audit traceability, dashboard monitoring, and "
        "hardware-ready decision packets for planned Verilog HDL enforcement."
    )

    try:
        (
            df,
            audit_df,
            hardware_df,
            feature_importance_df,
            model_comparison_df,
            model_metrics,
            audit_summary,
            best_model_summary
        ) = load_data()

    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()

    st.sidebar.title("Filters")

    risk_types = ["All"] + sorted(df["risk_type"].dropna().unique().tolist())
    actions = ["All", "ALLOW", "WARN", "BLOCK", "LOCK"]
    severities = ["All"] + sorted(df["severity"].dropna().unique().tolist())
    decision_sources = ["All"] + sorted(df["decision_source"].dropna().unique().tolist())

    selected_risk_type = st.sidebar.selectbox("Risk type", risk_types)
    selected_action = st.sidebar.selectbox("Final action", actions)
    selected_severity = st.sidebar.selectbox("Severity", severities)
    selected_decision_source = st.sidebar.selectbox("Decision source", decision_sources)

    min_final_score = st.sidebar.slider(
        "Minimum final risk score",
        min_value=0,
        max_value=100,
        value=0
    )

    filtered_df = df.copy()

    if selected_risk_type != "All":
        filtered_df = filtered_df[filtered_df["risk_type"] == selected_risk_type]

    if selected_action != "All":
        filtered_df = filtered_df[filtered_df["final_action"] == selected_action]

    if selected_severity != "All":
        filtered_df = filtered_df[filtered_df["severity"] == selected_severity]

    if selected_decision_source != "All":
        filtered_df = filtered_df[filtered_df["decision_source"] == selected_decision_source]

    filtered_df = filtered_df[filtered_df["final_risk_score"] >= min_final_score]

    total_transactions = len(filtered_df)

    allow_count = int((filtered_df["final_action"] == "ALLOW").sum())
    warn_count = int((filtered_df["final_action"] == "WARN").sum())
    block_count = int((filtered_df["final_action"] == "BLOCK").sum())
    lock_count = int((filtered_df["final_action"] == "LOCK").sum())

    st.divider()

    st.subheader("Security decision overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        metric_card("Transactions", f"{total_transactions:,}")

    with col2:
        metric_card("Allowed", f"{allow_count:,}")

    with col3:
        metric_card("Warned", f"{warn_count:,}")

    with col4:
        metric_card("Blocked", f"{block_count:,}")

    with col5:
        metric_card("Locked", f"{lock_count:,}")

    col6, col7, col8, col9 = st.columns(4)

    with col6:
        avg_ml_score = filtered_df["ml_fraud_score"].mean() if total_transactions else 0
        metric_card("Avg ML fraud score", round(avg_ml_score, 2))

    with col7:
        avg_rule_score = filtered_df["rule_risk_score"].mean() if total_transactions else 0
        metric_card("Avg rule risk score", round(avg_rule_score, 2))

    with col8:
        avg_final_score = filtered_df["final_risk_score"].mean() if total_transactions else 0
        metric_card("Avg final risk score", round(avg_final_score, 2))

    with col9:
        enforcement_count = int(filtered_df["final_action"].isin(["BLOCK", "LOCK"]).sum())
        enforcement_rate = enforcement_count / total_transactions if total_transactions else 0
        metric_card("Enforcement rate", format_percentage(enforcement_rate))

    anom1, anom2, anom3, anom4 = st.columns(4)

    with anom1:
        avg_autoencoder_score = (
            filtered_df["autoencoder_anomaly_score"].mean()
            if "autoencoder_anomaly_score" in filtered_df.columns and total_transactions
            else 0
        )
        metric_card("Avg autoencoder anomaly", round(avg_autoencoder_score, 2))

    with anom2:
        avg_isolation_score = (
            filtered_df["isolation_forest_anomaly_score"].mean()
            if "isolation_forest_anomaly_score" in filtered_df.columns and total_transactions
            else 0
        )
        metric_card("Avg isolation anomaly", round(avg_isolation_score, 2))

    with anom3:
        autoencoder_flags = (
            int((filtered_df["autoencoder_anomaly_score"] >= 70).sum())
            if "autoencoder_anomaly_score" in filtered_df.columns
            else 0
        )
        metric_card("Autoencoder flags", f"{autoencoder_flags:,}")

    with anom4:
        isolation_flags = (
            int((filtered_df["isolation_forest_anomaly_score"] >= 75).sum())
            if "isolation_forest_anomaly_score" in filtered_df.columns
            else 0
        )
        metric_card("Isolation flags", f"{isolation_flags:,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Final action distribution")
        action_distribution = (
            filtered_df["final_action"]
            .value_counts()
            .reindex(["ALLOW", "WARN", "BLOCK", "LOCK"])
            .fillna(0)
            .astype(int)
        )
        st.bar_chart(action_distribution)

    with right:
        st.subheader("Severity distribution")
        severity_distribution = filtered_df["severity"].value_counts()
        st.bar_chart(severity_distribution)

    left, right = st.columns(2)

    with left:
        st.subheader("Decision source distribution")
        source_distribution = filtered_df["decision_source"].value_counts()
        st.bar_chart(source_distribution)

    with right:
        st.subheader("Risk type distribution")
        risk_type_distribution = filtered_df["risk_type"].value_counts()
        st.bar_chart(risk_type_distribution)

    st.divider()

    st.subheader("Average scores by risk type")

    score_columns = safe_columns(
        filtered_df,
        [
            "ml_fraud_score",
            "rule_risk_score",
            "autoencoder_anomaly_score",
            "isolation_forest_anomaly_score",
            "final_risk_score"
        ]
    )

    if score_columns:
        score_summary = (
            filtered_df.groupby("risk_type")[score_columns]
            .mean()
            .round(2)
            .sort_values("final_risk_score", ascending=False)
        )

        st.dataframe(score_summary, width="stretch")
        st.bar_chart(score_summary)

    st.divider()

    st.subheader("Anomaly detection layer")

    st.caption(
        "The anomaly layer uses a deep autoencoder and Isolation Forest to detect unusual "
        "transaction behavior beyond supervised fraud classification."
    )

    anomaly_columns = safe_columns(
        filtered_df,
        [
            "autoencoder_anomaly_score",
            "isolation_forest_anomaly_score",
            "final_risk_score"
        ]
    )

    if anomaly_columns:
        anomaly_summary = (
            filtered_df.groupby("risk_type")[anomaly_columns]
            .mean()
            .round(2)
            .sort_values("final_risk_score", ascending=False)
        )

        st.dataframe(anomaly_summary, width="stretch")
        st.bar_chart(anomaly_summary)

    anomaly_severity_counts = audit_summary.get("anomaly_severity_counts", {})

    if anomaly_severity_counts:
        st.subheader("Anomaly severity distribution")

        anomaly_severity_df = pd.DataFrame(
            list(anomaly_severity_counts.items()),
            columns=["severity", "count"]
        ).set_index("severity")

        st.bar_chart(anomaly_severity_df)

    st.divider()

    st.subheader("Model benchmarking")

    st.caption(
        "This benchmark compares supervised ML, neural-network, and anomaly-detection "
        "models using fraud metrics and inference latency."
    )

    best_metrics = best_model_summary.get("metrics", {})
    best_model_name = best_model_summary.get("best_model_name", "NA")
    best_model_type = best_model_summary.get("best_model_type", "NA")

    best_cols = st.columns(6)

    with best_cols[0]:
        metric_card("Best model", best_model_name)

    with best_cols[1]:
        metric_card("Model type", best_model_type)

    with best_cols[2]:
        metric_card("Precision", best_metrics.get("precision", "NA"))

    with best_cols[3]:
        metric_card("Recall", best_metrics.get("recall", "NA"))

    with best_cols[4]:
        metric_card("F1 score", best_metrics.get("f1_score", "NA"))

    with best_cols[5]:
        metric_card("PR-AUC", best_metrics.get("average_precision", "NA"))

    latency_cols = st.columns(4)

    with latency_cols[0]:
        metric_card("False positives", best_metrics.get("false_positive", "NA"))

    with latency_cols[1]:
        metric_card("False negatives", best_metrics.get("false_negative", "NA"))

    with latency_cols[2]:
        metric_card("Latency / txn", best_metrics.get("latency_ms_per_transaction", "NA"))

    with latency_cols[3]:
        metric_card("Selection score", best_metrics.get("selection_score", "NA"))

    comparison_display_columns = safe_columns(
        model_comparison_df,
        [
            "model_name",
            "model_type",
            "accuracy",
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
    )

    st.dataframe(
        model_comparison_df[comparison_display_columns],
        width="stretch"
    )

    benchmark_chart_columns = safe_columns(
        model_comparison_df,
        [
            "precision",
            "recall",
            "f1_score",
            "average_precision",
            "selection_score"
        ]
    )

    if benchmark_chart_columns and "model_name" in model_comparison_df.columns:
        benchmark_chart_df = model_comparison_df.set_index("model_name")[benchmark_chart_columns]
        st.bar_chart(benchmark_chart_df)

    with st.expander("View best model summary JSON"):
        st.json(best_model_summary)

    st.divider()

    st.subheader("Primary Random Forest model performance")

    metric_cols = st.columns(6)

    with metric_cols[0]:
        metric_card("Accuracy", model_metrics.get("accuracy", "NA"))

    with metric_cols[1]:
        metric_card("Precision", model_metrics.get("precision", "NA"))

    with metric_cols[2]:
        metric_card("Recall", model_metrics.get("recall", "NA"))

    with metric_cols[3]:
        metric_card("F1 score", model_metrics.get("f1_score", "NA"))

    with metric_cols[4]:
        metric_card("ROC AUC", model_metrics.get("roc_auc", "NA"))

    with metric_cols[5]:
        metric_card("Avg precision", model_metrics.get("average_precision", "NA"))

    with st.expander("View confusion matrix and full primary model metrics"):
        st.json(model_metrics)

    st.subheader("Top feature importances")
    top_features = feature_importance_df.head(10).set_index("feature")
    st.bar_chart(top_features["importance"])
    st.dataframe(feature_importance_df, width="stretch")

    st.divider()

    st.subheader("High-risk transaction review")

    high_risk_df = filtered_df[
        filtered_df["final_action"].isin(["BLOCK", "LOCK"])
    ].sort_values(
        ["final_risk_score", "ml_fraud_score"],
        ascending=False
    )

    high_risk_columns = safe_columns(
        high_risk_df,
        [
            "transaction_id",
            "account_id",
            "timestamp",
            "risk_type",
            "amount",
            "ml_fraud_score",
            "model_confidence",
            "rule_risk_score",
            "autoencoder_anomaly_score",
            "isolation_forest_anomaly_score",
            "final_risk_score",
            "severity",
            "decision_source",
            "final_action",
            "final_reason"
        ]
    )

    st.dataframe(
        high_risk_df[high_risk_columns].head(100),
        width="stretch"
    )

    st.divider()

    st.subheader("Audit log view")

    filtered_audit_df = audit_df[
        audit_df["transaction_id"].isin(filtered_df["transaction_id"])
    ]

    audit_columns = safe_columns(
        filtered_audit_df,
        [
            "audit_id",
            "transaction_id",
            "timestamp",
            "severity",
            "decision_source",
            "amount",
            "rule_risk_score",
            "ml_fraud_score",
            "model_confidence",
            "autoencoder_anomaly_score",
            "isolation_forest_anomaly_score",
            "autoencoder_reconstruction_error",
            "final_risk_score",
            "rule_action",
            "final_action",
            "final_reason",
            "risk_type",
            "is_fraud"
        ]
    )

    st.dataframe(
        filtered_audit_df[audit_columns].head(200),
        width="stretch"
    )

    st.divider()

    st.subheader("Hardware-ready risk packets")

    st.caption(
        "These compact packets are designed to be consumed by the Verilog kill-switch engine later."
    )

    filtered_hardware_df = hardware_df[
        hardware_df["transaction_id"].isin(filtered_df["transaction_id"])
    ]

    st.dataframe(
        filtered_hardware_df.head(100),
        width="stretch"
    )

    st.divider()

    st.subheader("Audit summary")

    st.json(audit_summary)


if __name__ == "__main__":
    main()

# === FinShield Analyst Copilot Integration ===
try:
    from src.dashboard.copilot_tab import render_copilot_tab

    st.divider()
    with st.expander("FinShield Analyst Copilot", expanded=False):
        render_copilot_tab()

except Exception as copilot_error:
    st.warning(
        "FinShield Analyst Copilot could not be loaded. "
        "Core dashboard functionality is still available."
    )
    st.caption(f"Copilot load detail: {copilot_error}")
# === End FinShield Analyst Copilot Integration ===

