"""Click-based CLI for the Nexora MVP."""

from __future__ import annotations

from pathlib import Path

import click

from nexora import Nexora


@click.group()
def cli() -> None:
    """Nexora predictive analytics CLI."""


@cli.command()
@click.argument("data_csv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--target", required=True, help="Target column to predict.")
@click.option(
    "--out",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output .nx session path.",
)
@click.option(
    "--max-models",
    default=6,
    show_default=True,
    type=int,
    help="Maximum number of MVP registry models to train.",
)
def train(data_csv: Path, target: str, output_path: Path | None, max_models: int) -> None:
    """Train models from a CSV and save a Nexora session."""

    report = Nexora(data_csv, target=target).run(max_models=max_models)
    session_path = output_path or data_csv.with_suffix(".nx")
    saved = report.save(session_path)

    click.echo(f"Best model: {report.best_model} ({report.best_score_label}={report.best_score:.4f})")
    click.echo(f"Saved session: {saved}")
    click.echo("")
    leaderboard = report.leaderboard.head(10)
    click.echo(leaderboard.to_string(index=False))
