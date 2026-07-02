"""
Interactive CLI wizard for Nexora — mirrors the web frontend exactly.

Stages:
  1. Data Upload & Profiling
  2. Advanced Settings
  3. Target Selection & Task Detection
  4. Preprocessing Pipeline Display
  5. Model Battle Arena (training + live leaderboard)
  6. Prediction Studio
  7. SHAP Explanation
  8. Export
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.tree import Tree

from nexora import Nexora
from nexora.models.task_detector import detect_task_type
from nexora.profiler.dataset_profile import profile_dataset
from nexora.types import PreprocessingConfig

console = Console()

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════


def _bar(value: float, width: int = 20, color: str = "green") -> str:
    filled = int(value / 100 * width)
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (width - filled)}[/dim] {value:.0f}%"


def _score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _header(title: str, step: int, total: int = 9) -> None:
    console.print()
    console.rule(f"[bold cyan]Step {step}/{total}: {title}[/bold cyan]")
    console.print()


def _estimate_training_seconds(df: pd.DataFrame, max_models: int | None) -> int:
    models = max_models or 9
    rows = len(df)
    cols = len(df.columns)
    per_model = 1.0
    if rows > 2_000:
        per_model += 1.5
    if rows > 10_000:
        per_model += 4.0
    if cols > 30:
        per_model += 1.0
    if cols > 100:
        per_model += 3.0
    return max(5, int(models * per_model))


def _format_seconds(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = seconds // 60
    remainder = seconds % 60
    return f"{minutes} min {remainder} sec" if remainder else f"{minutes} min"


def _parse_model_selection(choice: str, options: list[dict]) -> list[str]:
    selected: list[str] = []
    for raw in choice.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            index = int(raw) - 1
        except ValueError:
            matches = [
                option["model_id"]
                for option in options
                if option["model_id"] == raw
                or option["model_name"].lower() == raw.lower()
            ]
            selected.extend(matches)
            continue
        if 0 <= index < len(options):
            selected.append(options[index]["model_id"])
    selected = list(dict.fromkeys(selected))
    if not selected:
        raise ValueError("Select at least one model.")
    if len(selected) > 5:
        raise ValueError("Choose one to five models.")
    return selected


def _dataframe_table(df: pd.DataFrame, title: str, max_rows: int = 20) -> Table:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    preview = df.head(max_rows)
    for column in preview.columns:
        table.add_column(str(column), max_width=24)
    for _, row in preview.iterrows():
        table.add_row(*[str(value)[:80] for value in row.tolist()])
    return table


# ═══════════════════════════════════════════════════════════════
# STAGE 1 — DATA UPLOAD & PROFILING
# ═══════════════════════════════════════════════════════════════


def _stage_data_upload() -> tuple[pd.DataFrame, Path, object]:
    """Prompt for CSV and profile instantly."""
    console.print(
        Panel.fit(
            "[bold magenta]✦ NEXORA[/bold magenta]  [dim]Autonomous Predictive Analytics Engine[/dim]\n"
            "[dim]Drop your CSV. We handle everything.[/dim]",
            border_style="magenta",
        )
    )

    data_path_str = Prompt.ask("\n[bold cyan]Enter path to your CSV file[/bold cyan]")
    data_path = Path(data_path_str.strip("\"'"))

    if not data_path.exists():
        console.print(f"[bold red]✗ File not found:[/] {data_path}")
        sys.exit(1)

    console.print(f"\n[dim]Loading {data_path.name}...[/dim]")
    df = pd.read_csv(data_path)
    console.print(
        f"[green]✓[/green] Loaded {len(df):,} rows × {len(df.columns)} columns\n"
    )

    with console.status("[bold green]Profiling dataset..."):
        prof = profile_dataset(df, source_name=data_path.name)

    # ── Health Score Panel ──
    sc = prof.health.overall
    console.print(
        Panel(
            f"[bold]Dataset Health Score[/bold]\n\n"
            f"  Overall          {_bar(sc, 30, _score_color(sc))}\n"
            f"  Missing Values   {_bar(prof.health.missing_values, 30, _score_color(prof.health.missing_values))}\n"
            f"  Data Quality     {_bar(prof.health.data_quality, 30, _score_color(prof.health.data_quality))}\n"
            f"  Prediction Ready {_bar(prof.health.prediction_readiness, 30, _score_color(prof.health.prediction_readiness))}\n"
            f"  Feature Quality  {_bar(prof.health.feature_quality, 30, _score_color(prof.health.feature_quality))}",
            title="[bold magenta]Data Quality Scorecard[/bold magenta]",
            border_style="magenta",
        )
    )

    # ── Missing Values by Column ──
    miss_table = Table(
        title="Missing Values by Column", show_header=True, header_style="bold cyan"
    )
    miss_table.add_column("Column", style="white")
    miss_table.add_column("Missing", justify="right")
    miss_table.add_column("Pct", justify="right")
    miss_table.add_column("Bar", min_width=20)
    for cp in prof.column_profiles:
        if cp.missing_count > 0:
            pct = cp.missing_pct
            miss_table.add_row(
                cp.name, str(cp.missing_count), f"{pct:.1f}%", _bar(pct, 15, "red")
            )
    if miss_table.row_count == 0:
        console.print("[green]✓ No missing values detected![/green]\n")
    else:
        console.print(miss_table)
        console.print()

    # ── Column Roles ──
    roles_table = Table(
        title="Column Roles", show_header=True, header_style="bold cyan"
    )
    roles_table.add_column("Column", style="white")
    roles_table.add_column("Type", style="green")
    roles_table.add_column("Role", style="yellow")
    roles_table.add_column("Unique", justify="right")
    roles_table.add_column("Samples", style="dim")
    for cp in prof.column_profiles:
        if cp.is_id_like:
            role = "🔑 ID"
        elif cp.is_datetime:
            role = "📅 Datetime"
        elif cp.is_numeric:
            role = "🔢 Numeric"
        elif cp.is_categorical:
            role = "🏷️  Categorical"
        else:
            role = "📝 Text"
        samples = ", ".join(str(s) for s in cp.sample_values[:3])
        roles_table.add_row(cp.name, cp.dtype, role, str(cp.unique_count), samples[:40])
    console.print(roles_table)
    console.print()

    # ── Strongest Relationships ──
    corr_data = prof.stats.get("correlation", {})
    if corr_data:
        pairs = []
        seen = set()
        for r, cols in corr_data.items():
            for c, v in cols.items():
                if r != c and v is not None and frozenset({r, c}) not in seen:
                    seen.add(frozenset({r, c}))
                    pairs.append((r, c, abs(v), v))
        pairs.sort(key=lambda x: x[2], reverse=True)
        if pairs:
            rel_table = Table(
                title="Strongest Relationships",
                show_header=True,
                header_style="bold cyan",
            )
            rel_table.add_column("Feature A")
            rel_table.add_column("Feature B")
            rel_table.add_column("Correlation", justify="right")
            rel_table.add_column("Strength")
            for a, b, absv, v in pairs[:5]:
                strength = (
                    "🔴 Strong"
                    if absv > 0.7
                    else ("🟡 Moderate" if absv > 0.4 else "🟢 Weak")
                )
                rel_table.add_row(a, b, f"{v:+.4f}", strength)
            console.print(rel_table)
            console.print()

    # ── Outlier Signals ──
    outlier_data = prof.stats.get("outlier_counts", {})
    if outlier_data and any(v > 0 for v in outlier_data.values()):
        out_table = Table(
            title="Outlier Signals (IQR Method)",
            show_header=True,
            header_style="bold cyan",
        )
        out_table.add_column("Column")
        out_table.add_column("Outliers", justify="right")
        out_table.add_column("% of rows", justify="right")
        for col, count in sorted(
            outlier_data.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                pct = count / len(df) * 100
                out_table.add_row(col, str(count), f"{pct:.1f}%")
        console.print(out_table)
        console.print()

    # ── Numeric Distribution ──
    numeric_cols = [cp.name for cp in prof.column_profiles if cp.is_numeric]
    if numeric_cols:
        dist_table = Table(
            title="Numeric Distribution by Percentile",
            show_header=True,
            header_style="bold cyan",
        )
        dist_table.add_column("Column")
        dist_table.add_column("Min", justify="right")
        dist_table.add_column("25%", justify="right")
        dist_table.add_column("50%", justify="right")
        dist_table.add_column("75%", justify="right")
        dist_table.add_column("Max", justify="right")
        dist_table.add_column("Mean", justify="right")
        dist_table.add_column("Std", justify="right")
        for col in numeric_cols[:8]:
            s = df[col].dropna()
            if len(s) == 0:
                continue
            q = s.quantile([0, 0.25, 0.5, 0.75, 1.0])
            dist_table.add_row(
                col,
                f"{q[0]:.2f}",
                f"{q[0.25]:.2f}",
                f"{q[0.5]:.2f}",
                f"{q[0.75]:.2f}",
                f"{q[1.0]:.2f}",
                f"{s.mean():.2f}",
                f"{s.std():.2f}",
            )
        console.print(dist_table)
        console.print()

    # ── Categorical Value Distribution ──
    cat_cols = [
        cp.name
        for cp in prof.column_profiles
        if cp.is_categorical and not cp.is_id_like
    ]
    if cat_cols:
        for col in cat_cols[:4]:
            counts = df[col].value_counts().head(6)
            cat_table = Table(
                title=f"'{col}' Value Distribution",
                show_header=True,
                header_style="bold cyan",
            )
            cat_table.add_column("Value")
            cat_table.add_column("Count", justify="right")
            cat_table.add_column("Pct", justify="right")
            cat_table.add_column("Bar", min_width=15)
            for val, cnt in counts.items():
                pct = cnt / len(df) * 100
                cat_table.add_row(
                    str(val), str(cnt), f"{pct:.1f}%", _bar(pct, 15, "cyan")
                )
            console.print(cat_table)
        console.print()

    # ── Suggested Targets ──
    suggested = _suggest_targets(df, prof)
    if suggested:
        console.print(
            Panel(
                "\n".join(
                    f"  [bold yellow]→[/bold yellow] {t['name']}  [dim]({t['reason']})[/dim]"
                    for t in suggested
                ),
                title="[bold green]Suggested Targets[/bold green]",
                border_style="green",
            )
        )

    # ── Model Readiness ──
    usable = sum(
        1
        for cp in prof.column_profiles
        if not cp.is_id_like and not cp.is_datetime and cp.unique_count > 1
    )
    readiness_text = (
        f"  Usable Features: [bold]{usable}[/bold]\n"
        f"  Rows:            [bold]{len(df):,}[/bold]\n"
    )
    if len(df) >= 100 and usable >= 2:
        readiness_text += (
            "  Status:          [bold green]✓ Ready for training[/bold green]\n"
        )
        families = ["Linear", "Tree-based", "Boosting (XGB/LGBM/CatBoost)"]
        if len(df) >= 500:
            families.append("Neural Networks")
        readiness_text += f"  Recommended:     {', '.join(families)}"
    else:
        readiness_text += "  Status:          [bold yellow]⚠ Limited — consider more data[/bold yellow]"
    console.print(
        Panel(
            readiness_text,
            title="[bold green]Model Readiness[/bold green]",
            border_style="green",
        )
    )

    # ── Dataset Preview ──
    preview_table = Table(
        title="Dataset Preview (first 5 rows)",
        show_header=True,
        header_style="bold cyan",
    )
    for col in df.columns:
        preview_table.add_column(col, max_width=15)
    for _, row in df.head(5).iterrows():
        preview_table.add_row(*[str(v)[:15] for v in row])
    console.print(preview_table)

    return df, data_path, prof


def _suggest_targets(df: pd.DataFrame, prof) -> list[dict]:
    """Heuristically suggest target columns."""
    suggestions = []
    for cp in prof.column_profiles:
        if cp.is_id_like or cp.is_datetime:
            continue
        name_lower = cp.name.lower()
        # Common target names
        if any(
            kw in name_lower
            for kw in [
                "target",
                "label",
                "class",
                "churn",
                "price",
                "revenue",
                "outcome",
                "result",
                "status",
                "default",
                "fraud",
            ]
        ):
            task = (
                "classification"
                if cp.is_categorical or cp.unique_count <= 10
                else "regression"
            )
            suggestions.append(
                {
                    "name": cp.name,
                    "reason": f"{task} — name suggests target",
                    "task": task,
                }
            )
        # Last column heuristic
    if not suggestions and len(prof.column_profiles) > 1:
        last = prof.column_profiles[-1]
        if not last.is_id_like:
            task = (
                "classification"
                if last.is_categorical or last.unique_count <= 10
                else "regression"
            )
            suggestions.append(
                {"name": last.name, "reason": f"{task} — last column", "task": task}
            )
    return suggestions[:5]


# ═══════════════════════════════════════════════════════════════
# STAGE 2 — ADVANCED SETTINGS
# ═══════════════════════════════════════════════════════════════


def _stage_settings() -> dict:
    """Ask for advanced training settings."""
    _header("Advanced Settings", 2)

    defaults = {
        "test_size": 0.2,
        "cv_folds": 5,
        "max_models": 6,
        "timeout": None,
        "random_seed": 42,
        "early_stopping": True,
        "preprocessing": PreprocessingConfig(),
    }

    settings_table = Table(
        title="Current Settings", show_header=True, header_style="bold cyan"
    )
    settings_table.add_column("Setting")
    settings_table.add_column("Value", justify="right", style="green")
    settings_table.add_row("Test Split Ratio", str(defaults["test_size"]))
    settings_table.add_row("Cross-Validation Folds", str(defaults["cv_folds"]))
    settings_table.add_row("Max Models", str(defaults["max_models"]))
    settings_table.add_row("Timeout (seconds)", str(defaults["timeout"] or "None"))
    settings_table.add_row("Random Seed", str(defaults["random_seed"]))
    settings_table.add_row(
        "Early Stopping", "✓ On" if defaults["early_stopping"] else "✗ Off"
    )
    console.print(settings_table)

    if Confirm.ask("Would you like to customize these settings?", default=False):
        try:
            if Confirm.ask("Reset settings to Nexora defaults first?", default=False):
                defaults = {
                    "test_size": 0.2,
                    "cv_folds": 5,
                    "max_models": 6,
                    "timeout": None,
                    "random_seed": 42,
                    "early_stopping": True,
                    "preprocessing": PreprocessingConfig(),
                }
            defaults["test_size"] = FloatPrompt.ask(
                "Test Split Ratio (0.1–0.4)", default=0.2
            )
            defaults["cv_folds"] = IntPrompt.ask("Cross-Validation Folds", default=5)
            defaults["max_models"] = IntPrompt.ask("Max Models to train", default=6)
            timeout = Prompt.ask(
                "Timeout per model in seconds (blank for none)", default=""
            )
            defaults["timeout"] = int(timeout) if timeout.strip() else None
            defaults["random_seed"] = IntPrompt.ask("Random Seed", default=42)
            defaults["early_stopping"] = Confirm.ask(
                "Enable Early Stopping?", default=True
            )
            scaling = Prompt.ask(
                "Feature Scaling",
                choices=["standard", "minmax", "none"],
                default=defaults["preprocessing"].scaling,
            )
            defaults["preprocessing"] = PreprocessingConfig(
                scaling=scaling,
                drop_id_columns=Confirm.ask("Drop ID-like columns?", default=True),
                remove_duplicates=Confirm.ask("Deduplicate rows?", default=True),
                fill_missing=Confirm.ask("Impute missing values?", default=True),
                outlier_cap=Confirm.ask("IQR outlier capping?", default=True),
                encode_categorical=Confirm.ask("Encode categoricals?", default=True),
            )
        except (KeyboardInterrupt, EOFError):
            console.print("[dim]Using defaults.[/dim]")

    return defaults


# ═══════════════════════════════════════════════════════════════
# STAGE 3 — TARGET SELECTION & TASK DETECTION
# ═══════════════════════════════════════════════════════════════


def _stage_target(df: pd.DataFrame, prof, suggested: list[dict]) -> tuple[str, str]:
    """Let user select target and confirm task type."""
    _header("Target Selection", 3)

    # Show suggested targets
    if suggested:
        console.print("[bold]Detected Targets:[/bold]")
        for i, s in enumerate(suggested, 1):
            console.print(
                f"  [bold yellow]{i}.[/bold yellow] {s['name']}  [dim]({s['reason']})[/dim]"
            )
        console.print()

    # List all columns
    console.print("[bold]All columns:[/bold]")
    col_names = [cp.name for cp in prof.column_profiles]
    for i, name in enumerate(col_names, 1):
        console.print(f"  {i:2d}. {name}")
    console.print()

    target = Prompt.ask("Select Target Column (name or number)")
    # Handle numeric input
    try:
        idx = int(target) - 1
        if 0 <= idx < len(col_names):
            target = col_names[idx]
    except ValueError:
        pass

    if target not in df.columns:
        console.print(f"[bold red]✗ Column '{target}' not found.[/]")
        sys.exit(1)

    # Task detection
    task = detect_task_type(df, target)
    unique_count = df[target].nunique()

    # Calculate confidence
    y = df[target].dropna()
    is_num = pd.api.types.is_numeric_dtype(y)
    if task == "classification":
        confidence = 95 if unique_count <= 5 else (85 if unique_count <= 20 else 70)
    else:
        confidence = 92 if is_num and unique_count > 50 else 78

    console.print(
        Panel(
            f"  Problem Type:  [bold green]{task.upper()}[/bold green]\n"
            f"  Confidence:    [bold]{confidence}%[/bold]\n"
            f"  Target:        [bold]{target}[/bold] · {unique_count} unique values · "
            f"{len([cp for cp in prof.column_profiles if cp.name != target and not cp.is_id_like])} features selected\n\n"
            f"  → {'Categorical target' if task == 'classification' else 'Continuous numeric target'}"
            f"{f' with {unique_count} classes' if task == 'classification' else ''}.",
            title="[bold magenta]Problem Type Detector[/bold magenta]",
            border_style="magenta",
        )
    )

    if not Confirm.ask(f"Is [bold]{task}[/bold] correct?", default=True):
        task = Prompt.ask(
            "Override problem type", choices=["classification", "regression"]
        )

    return target, task


# ═══════════════════════════════════════════════════════════════
# STAGE 4 — PREPROCESSING PIPELINE DISPLAY
# ═══════════════════════════════════════════════════════════════


def _stage_pipeline(df: pd.DataFrame, target: str, settings: dict) -> object:
    """Show preprocessing decisions and return the bundle."""
    _header("Automated Preprocessing Engine", 4)

    from nexora.preprocessing.pipeline_builder import build_preprocessing

    config = settings.get("preprocessing") or PreprocessingConfig()
    bundle = build_preprocessing(df, target, config=config)
    schema = bundle.schema

    # Pipeline tree
    tree = Tree("[bold magenta]Preprocessing Pipeline[/bold magenta]")

    missing_label = "Auto (median / mode)" if config.fill_missing else "Disabled"
    missing_branch = tree.add(f"🔧 Missing Values → [green]{missing_label}[/green]")
    for col in schema.numeric_features:
        missing_branch.add(f"[dim]{col}[/dim] → median imputation")
    for col in schema.categorical_features:
        missing_branch.add(f"[dim]{col}[/dim] → mode imputation")

    encode_label = "Label + One-Hot" if config.encode_categorical else "Disabled"
    encode_branch = tree.add(f"🏷️  Encoding → [green]{encode_label}[/green]")
    for col in schema.categorical_features:
        encode_branch.add(f"[dim]{col}[/dim] → OneHotEncoder")

    scale_label = {
        "standard": "StandardScaler",
        "minmax": "MinMaxScaler",
        "none": "None",
    }[config.scaling]
    scale_branch = tree.add(f"📏 Feature Scaling → [green]{scale_label}[/green]")
    for col in schema.numeric_features:
        scale_branch.add(f"[dim]{col}[/dim] → StandardScaler")

    tree.add(
        f"📊 Outliers → [green]{'IQR capping' if config.outlier_cap else 'Disabled'}[/green]"
    )
    tree.add(
        f"🧹 Duplicates → [green]{'Deduplicate rows' if config.remove_duplicates else 'Keep rows'}[/green]"
    )

    if schema.id_columns:
        drop_branch = tree.add("🗑️  Dropped Columns")
        for col in schema.id_columns:
            drop_branch.add(f"[dim]{col}[/dim] → [red]ID-like, removed[/red]")
    if schema.datetime_columns:
        dt_branch = tree.add("📅 Datetime Columns")
        for col in schema.datetime_columns:
            dt_branch.add(f"[dim]{col}[/dim] → [yellow]dropped (MVP)[/yellow]")

    console.print(tree)
    console.print()

    # Summary panel
    console.print(
        Panel(
            f"  Features selected:  [bold]{len(schema.feature_columns)}[/bold]\n"
            f"  Numeric:            [bold]{len(schema.numeric_features)}[/bold]\n"
            f"  Categorical:        [bold]{len(schema.categorical_features)}[/bold]\n"
            f"  Dropped:            [bold]{len(schema.dropped_columns)}[/bold]  "
            f"[dim]({', '.join(schema.dropped_columns) if schema.dropped_columns else 'none'})[/dim]",
            title="[bold green]Pipeline Summary[/bold green]",
            border_style="green",
        )
    )

    return bundle


# ═══════════════════════════════════════════════════════════════
# STAGE 5 — MODEL BATTLE ARENA
# ═══════════════════════════════════════════════════════════════


def _stage_battle_arena(
    df: pd.DataFrame, target: str, task: str, settings: dict
) -> object:
    """Train models with a live leaderboard."""
    _header("Model Battle Arena", 5)

    estimate = _estimate_training_seconds(df, settings.get("max_models", 6))
    console.print("[bold]🏟️  Launching Model Battle Arena...[/bold]")
    console.print(
        f"[dim]Expected time: about {_format_seconds(estimate)} for {settings.get('max_models', 6)} model(s).[/dim]\n"
    )

    progress_state = {"leaderboard": [], "current": "waiting"}

    def render_live() -> Table:
        table = Table(
            title=f"Live Leaderboard - {progress_state['current']}",
            show_header=True,
            header_style="bold yellow",
        )
        table.add_column("Rank", justify="center")
        table.add_column("Model")
        table.add_column("Family")
        table.add_column("Score", justify="right")
        table.add_column("Time", justify="right")
        table.add_column("Status")
        for rank, result in enumerate(progress_state["leaderboard"], 1):
            table.add_row(
                str(rank),
                result.model_name,
                result.family,
                f"{result.primary_score:.4f}",
                f"{result.train_time_sec:.3f}s",
                result.status,
            )
        return table

    def on_progress(event: dict) -> None:
        if event["event"] == "model_started":
            progress_state["current"] = (
                f"training {event['model_name']} ({event['index']}/{event['total']})"
            )
        elif event["event"] == "model_completed":
            result = event["result"]
            progress_state["current"] = f"finished {result.model_name}"
            progress_state["leaderboard"] = event.get(
                "leaderboard", progress_state["leaderboard"]
            )
        elif event["event"] == "training_complete":
            progress_state["current"] = "complete"

    nx = Nexora(df, target=target)
    with Live(render_live(), console=console, refresh_per_second=4) as live:

        def live_progress(event: dict) -> None:
            on_progress(event)
            live.update(render_live())

        report = nx.run(
            max_models=settings.get("max_models", 6),
            test_size=settings.get("test_size", 0.2),
            cv_folds=settings.get("cv_folds", 5),
            timeout_sec=settings.get("timeout"),
            random_state=settings.get("random_seed", 42),
            early_stopping=settings.get("early_stopping", True),
            problem_type=task,
            preprocessing_config=settings.get("preprocessing"),
            on_progress=live_progress,
        )

    # ── Live Leaderboard ──
    lb = report.leaderboard
    lb_table = Table(
        title="🏆 Live Leaderboard", show_header=True, header_style="bold yellow"
    )
    lb_table.add_column("Rank", justify="center", style="bold")
    lb_table.add_column("Model", style="white")
    lb_table.add_column("Family", style="cyan")
    lb_table.add_column(report.best_score_label.upper(), justify="right", style="green")
    lb_table.add_column("Time (s)", justify="right", style="dim")
    lb_table.add_column("Speed", justify="center")

    for _, row in lb.iterrows():
        rank = str(int(row["rank"])) if pd.notna(row["rank"]) else "-"
        medal = (
            "🥇"
            if rank == "1"
            else ("🥈" if rank == "2" else ("🥉" if rank == "3" else f" {rank}"))
        )
        speed_icon = "⚡" if row["speed"] == "fast" else "🔄"
        lb_table.add_row(
            medal,
            row["model_name"],
            row["family"],
            f"{row['primary_score']:.4f}",
            f"{row['train_time_sec']:.3f}",
            speed_icon,
        )
    console.print(lb_table)
    console.print()

    # ── Champion Declaration ──
    console.print(
        Panel(
            f"  🏆 Champion:  [bold yellow]{report.best_model}[/bold yellow]\n"
            f"  📊 Score:     [bold green]{report.best_score:.4f}[/bold green] ({report.best_score_label})\n"
            f"  ⏱️  Time:     {report.best_result.train_time_sec:.3f}s\n"
            f"  🏷️  Family:   {report.best_result.family}",
            title="[bold yellow]🏆 Champion Model[/bold yellow]",
            border_style="yellow",
        )
    )

    # ── Speed vs Score ──
    console.print("\n[bold]Speed vs Score Comparison:[/bold]")
    for _, row in lb.iterrows():
        score_bar_len = max(1, int(abs(row["primary_score"]) * 20))
        time_bar_len = max(1, min(20, int(row["train_time_sec"] * 5)))
        console.print(
            f"  {row['model_name']:30s} "
            f"Score [green]{'█' * score_bar_len}[/green] {row['primary_score']:.4f}  "
            f"Time [cyan]{'█' * time_bar_len}[/cyan] {row['train_time_sec']:.3f}s"
        )

    # ── Model Family Comparison ──
    families = {}
    for _, row in lb.iterrows():
        fam = row["family"]
        if fam not in families:
            families[fam] = []
        families[fam].append(row["primary_score"])

    console.print("\n[bold]Model Family Comparison:[/bold]")
    fam_table = Table(show_header=True, header_style="bold cyan")
    fam_table.add_column("Family")
    fam_table.add_column("Models", justify="right")
    fam_table.add_column(
        f"Best {report.best_score_label}", justify="right", style="green"
    )
    fam_table.add_column(f"Avg {report.best_score_label}", justify="right")
    for fam, scores in sorted(families.items(), key=lambda x: max(x[1]), reverse=True):
        fam_table.add_row(
            fam, str(len(scores)), f"{max(scores):.4f}", f"{np.mean(scores):.4f}"
        )
    console.print(fam_table)

    return report


# ═══════════════════════════════════════════════════════════════
# STAGE 6 — PREDICTION STUDIO
# ═══════════════════════════════════════════════════════════════


def _stage_prediction_studio(report, df: pd.DataFrame) -> None:
    """Interactive prediction with model selection and explanation."""
    _header("Prediction Studio", 6)

    if not Confirm.ask("Would you like to run predictions?", default=True):
        return

    model_options = report.available_prediction_models(limit=10)
    if not model_options:
        console.print(
            "[yellow]No completed models are available for Prediction Studio.[/yellow]"
        )
        return
    suggested = report.suggest_models(max_models=min(5, len(model_options)))
    suggested_ids = [item["model_id"] for item in suggested]
    model_table = Table(
        title="Select Models (choose one to five)",
        show_header=True,
        header_style="bold cyan",
    )
    model_table.add_column("#", justify="right")
    model_table.add_column("Model")
    model_table.add_column("Family")
    model_table.add_column("Score", justify="right")
    model_table.add_column("Suggested")
    for i, option in enumerate(model_options, 1):
        model_table.add_row(
            str(i),
            option["model_name"],
            option["family"],
            f"{option['primary_score']:.4f}",
            "yes" if option["model_id"] in suggested_ids else "",
        )
    console.print(model_table)
    default_choice = ",".join(
        str(model_options.index(opt) + 1)
        for opt in model_options
        if opt["model_id"] in suggested_ids[:3]
    )
    choice = Prompt.ask(
        "Models to use (numbers separated by comma)", default=default_choice or "1"
    )
    selected_models = _parse_model_selection(choice, model_options)

    console.print("\n[bold]Select prediction mode:[/bold]")
    console.print("  1. Predict from a new CSV file")
    console.print("  2. Enter values manually")
    mode = Prompt.ask("Choice", choices=["1", "2"], default="1")

    if mode == "1":
        csv_path = Prompt.ask("Path to new CSV file")
        path = Path(csv_path.strip("\"'"))
        if not path.exists():
            console.print("[bold red]File not found.[/]")
            return
        new_df = pd.read_csv(path)
        with console.status("[bold green]Running prediction..."):
            preds = report.predict_with_models(new_df, models=selected_models)
        console.print(_dataframe_table(preds, "Prediction Receipt (first 20 rows)"))
        if Confirm.ask("\nSave predictions to CSV?", default=True):
            out_path = Prompt.ask("Output file", default="predictions.csv")
            preds.to_csv(out_path, index=False)
            console.print(f"[green]✓ Saved to {out_path}[/green]")
        return
    else:
        # Manual entry
        console.print("\n[bold]Enter prediction inputs:[/bold]")
        row_data = {}
        for field in report.prediction_input_fields():
            suffix = ""
            if (
                field.kind == "number"
                and field.min_value is not None
                and field.max_value is not None
            ):
                suffix = f" [{field.min_value} to {field.max_value}]"
            elif field.options:
                suffix = f" [{', '.join(field.options[:6])}]"
            val = Prompt.ask(
                f"  {field.name}{suffix}", default=str(field.default or "")
            )
            # Try numeric
            try:
                val = float(val)
            except ValueError:
                pass
            row_data[field.name] = val

    # Prediction Receipt
    with console.status("[bold green]Running prediction..."):
        receipt = report.prediction_receipt(row_data, models=selected_models)

    receipt_table = Table(
        title="Prediction Receipt", show_header=True, header_style="bold green"
    )
    receipt_table.add_column("Model", style="cyan")
    receipt_table.add_column("Family")
    receipt_table.add_column("Prediction", style="bold yellow")
    receipt_table.add_column("Confidence", justify="right")
    for output in receipt.predictions:
        confidence = "-" if output.confidence is None else f"{output.confidence:.1%}"
        receipt_table.add_row(
            output.model_name,
            output.family,
            str(output.prediction),
            confidence,
        )
    console.print(receipt_table)
    console.print(
        Panel(
            f"Consensus: [bold yellow]{receipt.consensus}[/bold yellow]\n"
            f"Rule: {receipt.consensus_label}\n\n"
            f"{receipt.why}",
            title="[bold green]Why this prediction?[/bold green]",
            border_style="green",
        )
    )

    if receipt.contributions:
        contrib_table = Table(
            title="Local Contribution Signals",
            show_header=True,
            header_style="bold cyan",
        )
        contrib_table.add_column("Feature")
        contrib_table.add_column("Direction")
        contrib_table.add_column("Delta", justify="right")
        for item in receipt.contributions[:8]:
            contrib_table.add_row(
                item.feature, item.direction, f"{item.contribution:+.4f}"
            )
        console.print(contrib_table)

    # Why this prediction?
    if Confirm.ask(
        "\nWould you like to see why these predictions were made?", default=True
    ):
        try:
            importance = report.explain()
            console.print("\n[bold]Top contributing features:[/bold]")
            why_table = Table(show_header=True, header_style="bold cyan")
            why_table.add_column("Feature")
            why_table.add_column("Importance", justify="right", style="green")
            why_table.add_column("Impact")
            for _, row in importance.head(5).iterrows():
                imp = row.get("importance", row.iloc[-1]) if len(row) > 0 else 0
                bar_len = max(1, int(float(imp) * 50))
                why_table.add_row(
                    str(row.iloc[0]) if len(row) > 0 else "?",
                    f"{float(imp):.4f}",
                    f"[green]{'█' * bar_len}[/green]",
                )
            console.print(why_table)
        except Exception as e:
            console.print(f"[dim]Could not compute explanation: {e}[/dim]")


# ═══════════════════════════════════════════════════════════════
# STAGE 7 — SHAP EXPLANATION
# ═══════════════════════════════════════════════════════════════


def _stage_explain(report) -> None:
    """Show SHAP feature importance analysis."""
    _header("SHAP Explanation", 7)

    if not Confirm.ask("Show SHAP feature importance analysis?", default=True):
        return

    with console.status("[bold green]Computing SHAP values..."):
        try:
            importance = report.explain()
        except Exception as e:
            console.print(f"[yellow]⚠ SHAP unavailable: {e}[/yellow]")
            return

    if importance is None or (hasattr(importance, "empty") and importance.empty):
        console.print("[yellow]No importance data available.[/yellow]")
        return

    shap_table = Table(
        title="SHAP Feature Importance", show_header=True, header_style="bold magenta"
    )
    shap_table.add_column("Rank", justify="center", style="bold")
    shap_table.add_column("Feature", style="white")
    shap_table.add_column("Importance", justify="right", style="green")
    shap_table.add_column("Impact", min_width=25)

    for i, (_, row) in enumerate(importance.head(10).iterrows(), 1):
        feat_name = str(row.iloc[0]) if len(row) > 0 else "?"
        imp_val = float(row.iloc[-1]) if len(row) > 0 else 0
        bar_len = max(1, int(imp_val * 40))
        shap_table.add_row(
            str(i),
            feat_name,
            f"{imp_val:.4f}",
            f"[magenta]{'█' * bar_len}[/magenta]",
        )
    console.print(shap_table)

    console.print(
        Panel(
            f"The model [bold]{report.best_model}[/bold] relies most heavily on the features above.\n"
            f"Higher SHAP values indicate stronger influence on predictions.",
            title="[bold]Why does the champion model win?[/bold]",
            border_style="magenta",
        )
    )


def _stage_advanced_tracks(nx: Nexora, report, df: pd.DataFrame) -> None:
    """Optional experiment tracking, charts, clustering, and forecasts."""
    _header("Experiment Tracking & Advanced Tracks", 8, total=9)

    console.print(
        Panel(
            f"Run ID: [bold]{getattr(report.experiment_record, 'run_id', 'saved')}[/bold]\n"
            f"Best model: [bold]{report.best_model}[/bold]\n"
            f"Tracked runs: [bold]{len(Nexora.experiments())}[/bold]",
            title="[bold cyan]Experiment Tracking[/bold cyan]",
            border_style="cyan",
        )
    )

    if Confirm.ask("Save PNG charts for this terminal run?", default=False):
        chart_dir = Prompt.ask("Chart folder", default="nexora_charts")
        paths = report.save_charts(chart_dir)
        if paths:
            for path in paths:
                console.print(f"[green]✓[/green] {path}")
        else:
            console.print("[yellow]No chartable data found.[/yellow]")

    if Confirm.ask("Run clustering exploration?", default=False):
        try:
            n_clusters = IntPrompt.ask("Number of clusters", default=3)
            result = nx.cluster(n_clusters=n_clusters)
            table = Table(
                title="Cluster Profiles", show_header=True, header_style="bold cyan"
            )
            table.add_column("Cluster", justify="right")
            table.add_column("Size", justify="right")
            table.add_column("Pct", justify="right")
            table.add_column("Profile")
            for item in result["clusters"]:
                profile = ", ".join(f"{k}={v}" for k, v in item["profile"].items())
                table.add_row(
                    str(item["cluster"]),
                    str(item["size"]),
                    f"{item['percentage']}%",
                    profile[:100],
                )
            console.print(table)
            console.print(
                f"[dim]Silhouette: {result['metrics']['silhouette']} | Inertia: {result['metrics']['inertia']}[/dim]"
            )
        except Exception as e:
            console.print(f"[yellow]Clustering skipped: {e}[/yellow]")

    date_cols = [
        col
        for col in df.columns
        if pd.to_datetime(df[col].dropna().head(20), errors="coerce", format="mixed")
        .notna()
        .mean()
        > 0.8
        if len(df[col].dropna().head(20))
    ]
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if (
        date_cols
        and numeric_cols
        and Confirm.ask("Run simple forecast?", default=False)
    ):
        try:
            date_col = Prompt.ask("Date column", default=date_cols[0])
            target_col = Prompt.ask(
                "Numeric target column",
                default=report.target
                if report.target in numeric_cols
                else numeric_cols[0],
            )
            periods = IntPrompt.ask("Forecast periods", default=12)
            freq = Prompt.ask("Frequency", choices=["D", "W", "M"], default="M")
            forecast = nx.forecast(
                date_column=date_col,
                target_column=target_col,
                periods=periods,
                frequency=freq,
            )
            table = Table(title="Forecast", show_header=True, header_style="bold cyan")
            table.add_column("Date")
            table.add_column("Prediction", justify="right")
            for row in forecast["forecast"][:24]:
                table.add_row(row["date"], str(row["prediction"]))
            console.print(table)
            console.print(
                f"[dim]MAE: {forecast['metrics']['mae']} | R2: {forecast['metrics']['r2']}[/dim]"
            )
        except Exception as e:
            console.print(f"[yellow]Forecast skipped: {e}[/yellow]")


# ═══════════════════════════════════════════════════════════════
# STAGE 8 — EXPORT
# ═══════════════════════════════════════════════════════════════


def _stage_export(report, data_path: Path) -> None:
    """Save the terminal session and optionally export files."""
    _header("Export & Save", 9, total=9)

    # Save session
    session_path = data_path.with_suffix(".nx")
    report.save(session_path)
    console.print(f"[green]✓ Session saved:[/green] {session_path}")

    # PDF Report
    if Confirm.ask("Export full PDF report?", default=False):
        pdf_path = data_path.with_suffix(".pdf")
        report.to_pdf(pdf_path)
        console.print(f"[green]✓ PDF report:[/green] {pdf_path}")

    # Export Python code only
    if Confirm.ask("Generate standalone Python code?", default=False):
        code_path = data_path.with_suffix(".py")
        report.save_code(code_path)
        console.print(f"[green]✓ Python code:[/green] {code_path}")

    # Model pickle
    if Confirm.ask("Export model pickle (.pkl)?", default=False):
        pkl_path = data_path.with_suffix(".pkl")
        report.save_model(pkl_path)
        console.print(f"[green]✓ Model pickle:[/green] {pkl_path}")

    console.print()
    console.print(
        Panel.fit(
            "[bold green]✦ All done![/bold green]\n\n"
            f"  Session: {session_path}\n"
            f"  Best:    {report.best_model} ({report.best_score_label}={report.best_score:.4f})\n\n"
            "[dim]Run `nexora predict <session.nx> <new_data.csv>` to predict anytime.[/dim]",
            border_style="green",
        )
    )


# ═══════════════════════════════════════════════════════════════
# MAIN WIZARD ENTRY POINT
# ═══════════════════════════════════════════════════════════════


def run_wizard() -> None:
    """Run the full interactive Nexora wizard."""
    logo = """
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝

                 Autonomous AI Predictive Analytics Platform 
"""
    console.print(f"[bold #98ff98]{logo}[/bold #98ff98]")
    try:
        # Stage 1: Data Upload & Profiling
        df, data_path, prof = _stage_data_upload()
        suggested = _suggest_targets(df, prof)

        # Stage 2: Advanced Settings
        settings = _stage_settings()

        # Stage 3: Target Selection
        target, task = _stage_target(df, prof, suggested)

        # Stage 4: Preprocessing Pipeline
        _stage_pipeline(df, target, settings)

        # Stage 5: Model Battle Arena
        nx = Nexora(df, target=target)
        report = _stage_battle_arena(df, target, task, settings)

        # Stage 6: Prediction Studio
        _stage_prediction_studio(report, df)

        # Stage 7: SHAP Explanation
        _stage_explain(report)

        # Stage 8: Advanced Tracks
        _stage_advanced_tracks(nx, report, df)

        # Stage 9: Export
        _stage_export(report, data_path)

    except KeyboardInterrupt:
        console.print("\n[dim]Wizard cancelled by user.[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {e}")
        raise
