from __future__ import annotations

from click.testing import CliRunner

from nexora.cli.main import cli


def test_cli_train_saves_session(regression_csv, tmp_path):
    path, _ = regression_csv
    out = tmp_path / "trained.nx"
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["train", str(path), "--target", "revenue", "--max-models", "2", "--out", str(out)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert out.exists()
    assert "Best model:" in result.output
    assert "Saved session:" in result.output
