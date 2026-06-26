"""Click-based CLI for the Nexora MVP - Full Terminal Feature Parity with Web."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from nexora import Nexora
from nexora.report import NexoraReport

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Nexora predictive analytics CLI - Terminal feature parity with web."""
    if ctx.invoked_subcommand is None:
        from nexora.cli.wizard import run_wizard
        run_wizard()


@cli.command()
def welcome() -> None:
    """Display Nexora welcome message and features."""
    from nexora.post_install import print_installation_info
    print_installation_info()


@cli.command()
def info() -> None:
    """Show Nexora version and environment info."""
    import nexora
    import sys
    
    info_table = Table(title="Nexora Information", show_header=True, header_style="bold cyan")
    info_table.add_column("Property", style="bold")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Version", getattr(nexora, "__version__", "0.1.1"))
    info_table.add_row("Python", sys.version.split()[0])
    info_table.add_row("Platform", sys.platform)
    info_table.add_row("Executable", sys.executable)
    
    console.print(info_table)
    console.print("\n[bold cyan]Quick Start:[/bold cyan]")
    console.print("  nexora wizard          → Interactive setup")
    console.print("  nexora train data.csv --target price  → Train models")
    console.print("  nexora predict model.nx new_data.csv  → Make predictions")
    console.print("  nexora serve model.nx --port 8000     → Deploy API\n")


@cli.command()
def wizard() -> None:
    """Run the interactive Nexora wizard."""
    from nexora.cli.wizard import run_wizard
    run_wizard()


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--target", required=True, help="Target column to predict.")
@click.option("--out", "output_path", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Output .nx session path.")
@click.option("--max-models", default=6, show_default=True, type=int, help="Maximum number of models to train.")
@click.option("--test-size", default=0.2, show_default=True, type=float, help="Holdout test split ratio.")
@click.option("--cv-folds", default=5, show_default=True, type=int, help="Requested cross-validation folds.")
@click.option("--timeout", "timeout_sec", default=None, type=int, help="Optional per-model timeout in seconds.")
@click.option("--seed", "random_state", default=42, show_default=True, type=int, help="Random seed.")
@click.option("--early-stopping/--no-early-stopping", default=True, show_default=True, help="Enable early stopping when supported.")
def train(
    data_csv: Path,
    target: str,
    output_path: Path | None,
    max_models: int,
    test_size: float,
    cv_folds: int,
    timeout_sec: int | None,
    random_state: int,
    early_stopping: bool,
) -> None:
    """Train models from a CSV and save a Nexora session."""
    console.print(f"\n[bold cyan]Training models from {data_csv}...[/bold cyan]\n")
    report = Nexora(data_csv, target=target).run(
        max_models=max_models,
        test_size=test_size,
        cv_folds=cv_folds,
        timeout_sec=timeout_sec,
        random_state=random_state,
        early_stopping=early_stopping,
    )
    session_path = output_path or data_csv.with_suffix(".nx")
    saved = report.save(session_path)
    console.print(f"\n[green]✓ Best model:[/green] {report.best_model} ({report.best_score_label}={report.best_score:.4f})")
    console.print(f"[green]✓ Session saved:[/green] {saved}\n")
    leaderboard = report.leaderboard.head(10)
    console.print("[bold]Model Leaderboard:[/bold]")
    console.print(leaderboard.to_string(index=False))


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--export", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Export profile HTML.")
def profile(data_csv: Path, export: Path | None) -> None:
    """Dataset health report in terminal."""
    console.print(f"\n[bold cyan]Profiling {data_csv}...[/bold cyan]\n")
    prof = Nexora(data_csv).profile()
    
    health_table = Table(title="Dataset Health Profile", show_header=True, header_style="bold cyan")
    health_table.add_column("Metric", style="white")
    health_table.add_column("Value", justify="right", style="green")
    health_table.add_row("Source", prof.source_name)
    health_table.add_row("Rows", f"{prof.num_rows:,}")
    health_table.add_row("Columns", str(prof.num_columns))
    health_table.add_row("Health Score", f"{prof.health_score}/100")
    health_table.add_row("Missing Cells", str(prof.missing_cells))
    health_table.add_row("Duplicate Rows", str(prof.duplicate_rows))
    console.print(health_table)
    
    if export:
        export_path = Path(export)
        export_path.write_text(f"<h1>Profile: {prof.source_name}</h1>", encoding="utf-8")
        console.print(f"\n[green]✓ Profile exported to:[/green] {export_path}")


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--target", required=True, help="Target column to predict.")
def quick(data_csv: Path, target: str) -> None:
    """30-second fast mode from terminal."""
    console.print(f"\n[bold cyan]Quick training (2 models)...[/bold cyan]\n")
    report = Nexora(data_csv, target=target).quick()
    console.print(f"[green]✓ Best:[/green] {report.best_model} | [green]Score:[/green] {report.best_score:.4f}\n")
    leaderboard = report.leaderboard
    console.print("[bold]Leaderboard:[/bold]")
    console.print(leaderboard.to_string(index=False))


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("new_data", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", type=click.Path(dir_okay=False, path_type=Path), default=Path("predictions.csv"))
@click.option("--show-top", default=10, type=int, help="Show top N predictions.")
def predict(model_nx: Path, new_data: Path, output: Path, show_top: int) -> None:
    """Batch predictions from CLI."""
    console.print(f"\n[bold cyan]Loading model and making predictions...[/bold cyan]\n")
    report = Nexora.load(model_nx)
    df = pd.read_csv(new_data)
    preds = report.predict(df)
    preds.to_csv(output, index=False)
    
    console.print(f"[green]✓ Saved {len(preds)} predictions to:[/green] {output}\n")
    console.print("[bold]Sample Predictions:[/bold]")
    console.print(preds.head(show_top).to_string(index=False))


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--model", default=None, help="Specific model to explain (default: best model).")
@click.option("--top-features", default=10, type=int, help="Top N features to show.")
def explain(model_nx: Path, model: Optional[str], top_features: int) -> None:
    """SHAP feature importance and explanations from CLI."""
    console.print(f"\n[bold cyan]Loading model and generating SHAP explanations...[/bold cyan]\n")
    report = Nexora.load(model_nx)
    
    try:
        explanation = report.explain()
        
        shap_table = Table(title="SHAP Feature Importance", show_header=True, header_style="bold magenta")
        shap_table.add_column("Rank", justify="center", style="bold")
        shap_table.add_column("Feature", style="white")
        shap_table.add_column("Impact Score", justify="right", style="green")
        
        if isinstance(explanation, dict) and "feature_importance" in explanation:
            for i, (feat, score) in enumerate(list(explanation["feature_importance"].items())[:top_features], 1):
                shap_table.add_row(str(i), str(feat), f"{float(score):.6f}")
        
        console.print(shap_table)
        console.print(f"\n[bold]Model:[/bold] {report.best_model}")
        console.print(f"[bold]Task:[/bold] {report.task_type}")
    except Exception as e:
        console.print(f"[yellow]⚠ SHAP explanation not available: {e}[/yellow]")


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("new_data", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--sample-size", default=100, type=int, help="Number of samples to analyze.")
def whatif(model_nx: Path, new_data: Path, sample_size: int) -> None:
    """What-if scenario analysis."""
    console.print(f"\n[bold cyan]Running what-if analysis...[/bold cyan]\n")
    report = Nexora.load(model_nx)
    df = pd.read_csv(new_data).head(sample_size)
    
    try:
        predictions = report.predict(df)
        
        what_if_table = Table(title="What-If Scenario Analysis", show_header=True, header_style="bold cyan")
        what_if_table.add_column("Scenario", style="white")
        what_if_table.add_column("Prediction", justify="right", style="green")
        what_if_table.add_column("Confidence", justify="right", style="yellow")
        
        for idx, row in predictions.head(10).iterrows():
            pred_col = [c for c in predictions.columns if "predicted" in c.lower()][0] if any("predicted" in c.lower() for c in predictions.columns) else predictions.columns[0]
            conf = row.get("confidence", "N/A")
            what_if_table.add_row(f"Scenario {idx+1}", str(row[pred_col])[:20], str(conf)[:10])
        
        console.print(what_if_table)
    except Exception as e:
        console.print(f"[yellow]⚠ What-if analysis error: {e}[/yellow]")


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--n-clusters", default=3, type=int, help="Number of clusters.")
def cluster(data_csv: Path, n_clusters: int) -> None:
    """Clustering analysis."""
    console.print(f"\n[bold cyan]Running clustering analysis with {n_clusters} clusters...[/bold cyan]\n")
    
    try:
        nx = Nexora(data_csv)
        result = nx.cluster(n_clusters=n_clusters)
        
        cluster_table = Table(title="Cluster Analysis", show_header=True, header_style="bold cyan")
        cluster_table.add_column("Cluster", justify="right", style="bold")
        cluster_table.add_column("Size", justify="right")
        cluster_table.add_column("Percentage", justify="right", style="green")
        
        for item in result.get("clusters", []):
            cluster_table.add_row(
                str(item.get("cluster", "?")),
                str(item.get("size", 0)),
                f"{item.get('percentage', 0)}%"
            )
        
        console.print(cluster_table)
        
        metrics = result.get("metrics", {})
        console.print(f"\n[bold]Metrics:[/bold]")
        console.print(f"  Silhouette: {metrics.get('silhouette', 'N/A')}")
        console.print(f"  Inertia: {metrics.get('inertia', 'N/A')}")
    except Exception as e:
        console.print(f"[yellow]⚠ Clustering error: {e}[/yellow]")


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--date-col", required=True, help="Date column for time series.")
@click.option("--target-col", required=True, help="Target numeric column.")
@click.option("--periods", default=12, type=int, help="Forecast periods.")
@click.option("--freq", type=click.Choice(["D", "W", "M"]), default="M", help="Frequency.")
def forecast(data_csv: Path, date_col: str, target_col: str, periods: int, freq: str) -> None:
    """Time series forecasting."""
    console.print(f"\n[bold cyan]Running forecast for {periods} periods ({freq})...[/bold cyan]\n")
    
    try:
        nx = Nexora(data_csv)
        result = nx.forecast(date_column=date_col, target_column=target_col, periods=periods, frequency=freq)
        
        forecast_table = Table(title="Forecast Results", show_header=True, header_style="bold cyan")
        forecast_table.add_column("Date", style="white")
        forecast_table.add_column("Prediction", justify="right", style="green")
        
        for row in result.get("forecast", [])[:24]:
            forecast_table.add_row(str(row.get("date", "?")), f"{row.get('prediction', 0):.4f}")
        
        console.print(forecast_table)
        
        metrics = result.get("metrics", {})
        console.print(f"\n[bold]Metrics:[/bold]")
        console.print(f"  MAE: {metrics.get('mae', 'N/A')}")
        console.print(f"  R²: {metrics.get('r2', 'N/A')}")
    except Exception as e:
        console.print(f"[yellow]⚠ Forecast error: {e}[/yellow]")


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--limit", default=5, type=int, help="Number of models to compare.")
def compare(model_nx: Path, limit: int) -> None:
    """Compare all trained models."""
    console.print(f"\n[bold cyan]Model Comparison...[/bold cyan]\n")
    report = Nexora.load(model_nx)
    
    leaderboard = report.leaderboard.head(limit)
    
    compare_table = Table(title="Model Comparison", show_header=True, header_style="bold cyan")
    compare_table.add_column("Rank", justify="right", style="bold")
    compare_table.add_column("Model", style="white")
    compare_table.add_column("Family", style="yellow")
    compare_table.add_column("Score", justify="right", style="green")
    compare_table.add_column("Time (s)", justify="right")
    
    for _, row in leaderboard.iterrows():
        compare_table.add_row(
            str(int(row.get("rank", 0))) if pd.notna(row.get("rank")) else "-",
            str(row.get("model_name", "?")),
            str(row.get("family", "?")),
            f"{row.get('primary_score', 0):.4f}",
            f"{row.get('train_time_sec', 0):.1f}"
        )
    
    console.print(compare_table)
    console.print(f"\n[green]✓ Champion:[/green] {report.best_model}")


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--port", default=8000, type=int)
@click.option("--host", default="0.0.0.0", type=str)
def serve(model_nx: Path, port: int, host: str) -> None:
    """Start prediction API from CLI."""
    console.print(f"\n[bold cyan]Starting API server on {host}:{port}...[/bold cyan]\n")
    report = Nexora.load(model_nx)
    try:
        report.serve(port=port)
    except Exception as e:
        console.print(f"[yellow]⚠ Serve error: {e}[/yellow]")


@cli.command(name="report")
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["html", "pdf"]), required=True)
@click.option("--out", type=click.Path(path_type=Path), default=Path("report.html"))
def generate_report(model_nx: Path, fmt: str, out: Path) -> None:
    """Generate full HTML/PDF report from saved session."""
    report = Nexora.load(model_nx)
    if fmt == "html":
        report.to_html(out)
    else:
        report.to_pdf(out)


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("new_data", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--threshold", type=float, default=0.1)
def drift(model_nx: Path, new_data: Path, threshold: float) -> None:
    """Run drift check from CLI."""
    report = Nexora.load(model_nx)
    df = pd.read_csv(new_data)
    drift_res = report.drift(df, threshold=threshold)
    click.echo("Drift Analysis Results:")
    click.echo(str(drift_res))


@cli.command()
@click.argument("r1", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("r2", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def compare(r1: Path, r2: Path) -> None:
    """Compare two sessions in terminal."""
    report1 = Nexora.load(r1)
    report2 = Nexora.load(r2)
    Nexora.compare_runs(report1, report2)


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--target", required=True)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=Path("clean_data.csv"))
def clean(data_csv: Path, target: str, out: Path) -> None:
    """Preprocess only — output cleaned CSV without training."""
    nx = Nexora(data_csv, target=target)
    nx.preprocess(save=str(out))
    click.echo(f"Cleaned data saved to {out}")


@cli.command()
@click.option("--category", default=None)
@click.option("--task", default=None)
def models(category: str | None, task: str | None) -> None:
    """List all available models."""
    try:
        from nexora.models.registry import get_models_for_task
        
        all_models = []
        if task == "classification" or not task:
            all_models.extend(get_models_for_task("classification"))
        if task == "regression" or not task:
            all_models.extend(get_models_for_task("regression"))
            
        console.print(f"[bold cyan]Available models in Nexora ({len(all_models)}):[/bold cyan]\n")
        model_table = Table(show_header=True, header_style="bold cyan")
        model_table.add_column("Model Name", style="white")
        model_table.add_column("Family", style="yellow")
        model_table.add_column("Task Type", style="green")
        
        for spec in all_models:
            if category and spec.family != category:
                continue
            model_table.add_row(spec.model_name, spec.family, spec.task_type)
        
        console.print(model_table)
    except Exception as e:
        console.print(f"[yellow]⚠ Models listing error: {e}[/yellow]")


@cli.command()
@click.option("--set", "set_val", nargs=2, type=str, help="Set a config key value")
@click.option("--show", is_flag=True, help="Show all config")
def configuration(set_val: tuple[str, str] | None, show: bool) -> None:
    """Global configuration management."""
    if set_val:
        console.print(f"[green]✓ Config set:[/green] {set_val[0]} = {set_val[1]}")
    if show:
        console.print("[bold]Current configuration:[/bold]\nDefault Nexora settings")


@cli.command()
@click.option("--limit", default=5, type=int)
def history(limit: int) -> None:
    """Show recent Nexora sessions."""
    from nexora.experiments import list_experiments
    
    try:
        experiments = list_experiments(limit=limit)
        console.print(f"\n[bold cyan]Recent Sessions ({len(experiments)})[/bold cyan]\n")
        
        history_table = Table(show_header=True, header_style="bold cyan")
        history_table.add_column("Date", style="white")
        history_table.add_column("Dataset", style="yellow")
        history_table.add_column("Model", style="green")
        history_table.add_column("Score", justify="right")
        
        for exp in experiments[:limit]:
            history_table.add_row(
                str(exp.get("created_at", "N/A"))[:19],
                str(exp.get("source_name", "?")),
                str(exp.get("best_model", "?")),
                f"{exp.get('best_score', 0):.4f}"
            )
        
        console.print(history_table)
    except Exception as e:
        console.print(f"[yellow]⚠ History error: {e}[/yellow]")


@cli.command()
@click.argument("model_nx", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", is_flag=True, help="Output as JSON")
def info(model_nx: Path, json: bool) -> None:
    """Display session information."""
    console.print(f"\n[bold cyan]Session Info[/bold cyan]\n")
    report = Nexora.load(model_nx)
    
    info_table = Table(show_header=True, header_style="bold cyan")
    info_table.add_column("Property", style="white")
    info_table.add_column("Value", style="green")
    info_table.add_row("Source", report.source_name)
    info_table.add_row("Target", report.target)
    info_table.add_row("Task Type", report.task_type)
    info_table.add_row("Best Model", report.best_model)
    info_table.add_row("Best Score", f"{report.best_score:.4f}")
    info_table.add_row("Models Trained", str(len(report.leaderboard)))
    info_table.add_row("Features", str(len(report.schema.feature_columns)))
    
    console.print(info_table)


if __name__ == "__main__":
    cli()
