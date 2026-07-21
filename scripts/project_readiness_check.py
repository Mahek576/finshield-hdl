from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CURRENT_FILE = Path(__file__).resolve()

EXCLUDED_DIRS = {
    ".git",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "run_pipeline.py",
    "scripts/run_finshield_demo.py",
    "scripts/project_readiness_check.py",
    "src/api/main.py",
    "src/api/schemas.py",
    "src/risk/cost_engine.py",
    "src/monitoring/drift_monitor.py",
    "src/llm/copilot_service.py",
    "src/dashboard/copilot_tab.py",
    "docs/model_card.md",
    "docs/final_project_report.md",
    "docs/demo_guide.md",
    "docs/deployment_guide.md",
    ".github/workflows/tests.yml",
    "Dockerfile",
    "docker-compose.yml",
]


def blocked_terms() -> List[str]:
    # Built by concatenation so this checker does not match itself.
    return [
        "Ver" + "ilog",
        "Viv" + "ado",
        "H" + "D" + "L",
        "F" + "P" + "G" + "A",
        "hard" + "ware-ready",
        "kill" + "-switch",
        "ver" + "ilog_decision",
        "hard" + "ware_risk",
        "hard" + "ware packet",
        "hard" + "ware packets",
    ]


def iter_project_files() -> Iterable[Path]:
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        resolved_path = path.resolve()

        if resolved_path == CURRENT_FILE:
            continue

        if any(part in EXCLUDED_DIRS for part in resolved_path.parts):
            continue

        yield resolved_path


def scan_disallowed_terms() -> List[str]:
    findings: List[str] = []
    terms = blocked_terms()

    for path in iter_project_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lower_text = text.lower()

        for term in terms:
            if term.lower() in lower_text:
                rel_path = path.relative_to(PROJECT_ROOT)
                findings.append(f"{rel_path}: contains blocked legacy wording")
                break

    return findings


def check_required_files() -> List[str]:
    missing: List[str] = []

    for file_path in REQUIRED_FILES:
        if not (PROJECT_ROOT / file_path).exists():
            missing.append(file_path)

    return missing


def main() -> None:
    print("Running FinShield project readiness check...")

    missing = check_required_files()
    findings = scan_disallowed_terms()

    if missing:
        print("\nMissing required files:")
        for item in missing:
            print(f"- {item}")

    if findings:
        print("\nBlocked legacy wording found:")
        for item in findings:
            print(f"- {item}")

    if missing or findings:
        raise SystemExit(1)

    print("Readiness check passed.")
    print("FinShield is clean, AI/ML-focused, and presentation-ready.")


if __name__ == "__main__":
    main()
