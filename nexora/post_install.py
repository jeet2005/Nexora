"""
Post-install script that displays Nexora features and installation metrics.
Run automatically after pip install nexora-prediction.
"""

import sys
import time
from datetime import datetime

NEXORA_LOGO = """
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝
"""

FEATURES = {
    "Core ML": [
        "18+ classification & regression models",
        "XGBoost, LightGBM, CatBoost, scikit-learn",
        "Automatic hyperparameter tuning (Optuna)",
        "Stratified cross-validation & train/test split",
    ],
    "Data Analysis": [
        "Auto-detect task type (classification/regression)",
        "Handle missing values, encoding, scaling",
        "Dataset health scoring & profiling",
        "Outlier detection & deduplication",
    ],
    "Explainability": [
        "SHAP feature importance analysis",
        "Permutation importance fallback",
        "Partial dependence plots",
        "What-if scenario analysis",
    ],
    "Production Ready": [
        "REST API deployment (FastAPI/Flask)",
        "Docker containerization",
        "Model serialization & versioning",
        "Drift detection & monitoring",
    ],
    "Analytics & Reporting": [
        "HTML/PDF report generation",
        "Model leaderboard comparison",
        "Confusion matrices & ROC curves",
        "Learning curve analysis",
    ],
    "CLI Interface": [
        "20+ terminal commands",
        "Interactive 9-stage wizard",
        "No browser required",
        "Full Python API for automation",
    ],
    "AI Integration": [
        "LLM-powered explanations (OpenAI/Claude/Ollama)",
        "Natural language insights",
        "Educational assistant chat",
        "Grounded AI interactions",
    ],
    "Data Connectors": [
        "CSV, Excel, Parquet, JSON, SQL",
        "MongoDB, S3, Google Sheets",
        "scikit-learn datasets",
        "100+ format support",
    ],
}

INSTALLATION_TIMES = {
    "Fast Install (core only)": "~30 seconds",
    "Standard Install (recommended)": "~2-3 minutes",
    "Full Install (all extras)": "~5-8 minutes",
    "Development Setup": "~10 minutes",
}

QUICK_START_COMMANDS = [
    ("Interactive Wizard", "nexora wizard"),
    ("Profile Dataset", "nexora profile data.csv"),
    ("Train Models", "nexora train data.csv --target price"),
    ("Make Predictions", "nexora predict model.nx new_data.csv"),
    ("Deploy API", "nexora serve model.nx --port 8000"),
    ("View Python Docs", "python -c \"from nexora import Nexora; help(Nexora)\""),
]

def print_section(title: str, color: str = "green"):
    """Print a formatted section header."""
    colors = {
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    color_code = colors.get(color, "")
    reset_code = colors["reset"]
    print(f"\n{color_code}{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}{reset_code}\n")

def print_installation_info():
    """Print installation information."""
    print_section("INSTALLATION SUCCESSFUL!", "green")
    print(NEXORA_LOGO)
    print("\nWelcome to Nexora - Autonomous AI Predictive Analytics Platform\n")

    # Installation time estimates
    print_section("Expected Installation Times", "blue")
    for scenario, time_est in INSTALLATION_TIMES.items():
        print(f"  • {scenario:<35} {time_est:>20}")

    # Features breakdown
    print_section("Included Features", "cyan")
    for category, items in FEATURES.items():
        print(f"{category}")
        for item in items:
            print(f"  [*] {item}")
        print()

    # Quick start
    print_section("Quick Start Commands", "yellow")
    for description, command in QUICK_START_COMMANDS:
        print(f"  {description:<25} → nexora {command.replace('nexora ', '')}")

    # Next steps
    print_section("Next Steps", "green")
    print("  1. Run the interactive wizard:")
    print("     $ nexora wizard\n")
    print("  2. Or use direct commands:")
    print("     $ nexora train data.csv --target price\n")
    print("  3. Read documentation:")
    print("     $ nexora --help\n")
    print("  4. View Python API:")
    print("     $ python -c \"from nexora import Nexora; help(Nexora)\"\n")

    # Resources
    print_section("Resources", "cyan")
    print("  Documentation:  https://github.com/jeet2005/nexora/blob/main/QUICK_START.md")
    print("  CLI Reference:  https://github.com/jeet2005/nexora/blob/main/CLI_FEATURES.md")
    print("  GitHub:         https://github.com/jeet2005/nexora")
    print("  Issues/Support: https://github.com/jeet2005/nexora/issues\n")

    # Optional dependencies
    print_section("Optional Features", "blue")
    print("  Install extra capabilities with:\n")
    print("  $ pip install nexora-prediction[sql]      # PostgreSQL, MySQL, SQLite")
    print("  $ pip install nexora-prediction[mongo]    # MongoDB support")
    print("  $ pip install nexora-prediction[cloud]    # AWS S3, Google Sheets")
    print("  $ pip install nexora-prediction[ui]       # Streamlit web interface")
    print("  $ pip install nexora-prediction[llm]      # OpenAI, Claude, Ollama")
    print("  $ pip install nexora-prediction[export]   # Advanced PDF/Notebook export")
    print("  $ pip install nexora-prediction[all]      # All optional features\n")

    # Version info
    print_section("Version & Status", "green")
    try:
        import nexora
        print(f"  Nexora Version:  {nexora.__version__}")
    except:
        print(f"  Nexora Version:  0.1.1")
    print(f"  Python Version:  {sys.version.split()[0]}")
    print(f"  Installation:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print_section("You're All Set!", "green")
    print("  Start analyzing your data in seconds!\n")

if __name__ == "__main__":
    print_installation_info()
