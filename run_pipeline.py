from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent


PIPELINE_STEPS = [
    {
        "name": "Generate synthetic transactions",
        "command": ["src/data/generate_transactions.py"]
    },
    {
        "name": "Apply cybersecurity risk rules",
        "command": ["src/rules/risk_rules.py"]
    },
    {
        "name": "Train primary ML fraud model",
        "command": ["src/ml/train_model.py"]
    },
    {
        "name": "Benchmark ML and anomaly detection models",
        "command": ["src/ml/benchmark_models.py"]
    },
    {
        "name": "Run hybrid final decision engine",
        "command": ["src/rules/final_decision_engine.py"]
    },
    {
        "name": "Generate audit logs",
        "command": ["src/audit/audit_logger.py"]
    }
]


def run_step(step_number, step):
    print("=" * 80)
    print(f"Step {step_number}: {step['name']}")
    print("=" * 80)

    start_time = time.time()

    command = [sys.executable] + step["command"]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True
    )

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    if result.returncode != 0:
        print()
        print(f"Pipeline failed at step {step_number}: {step['name']}")
        print(f"Exit code: {result.returncode}")
        sys.exit(result.returncode)

    print()
    print(f"Completed: {step['name']} in {elapsed_time} seconds")
    print()


def main():
    print()
    print("Starting FinShield HDL pipeline...")
    print(f"Project root: {PROJECT_ROOT}")
    print()

    pipeline_start = time.time()

    for index, step in enumerate(PIPELINE_STEPS, start=1):
        run_step(index, step)

    pipeline_end = time.time()
    total_time = round(pipeline_end - pipeline_start, 2)

    print("=" * 80)
    print("FinShield HDL pipeline completed successfully.")
    print("=" * 80)
    print(f"Total runtime: {total_time} seconds")
    print()
    print("Generated outputs:")
    print("data/sample_transactions.csv")
    print("data/processed/rule_scored_transactions.csv")
    print("data/processed/verilog_decision_packets.csv")
    print("data/processed/ml_scored_transactions.csv")
    print("data/processed/benchmark_scored_transactions.csv")
    print("data/processed/final_decision_transactions.csv")
    print("data/processed/hardware_risk_packets.csv")
    print("data/processed/audit_log_view.csv")
    print("results/model_metrics.json")
    print("results/feature_importance.csv")
    print("results/model_comparison.csv")
    print("results/model_comparison.json")
    print("results/best_model_summary.json")
    print("results/audit_logs.jsonl")
    print("results/audit_summary.json")
    print()
    print("To open the dashboard, run:")
    print("streamlit run src/dashboard/app.py")


if __name__ == "__main__":
    main()