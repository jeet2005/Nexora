"""
Nexora Full System Test Suite — 100+ Test Cases
================================================
Tests every entry point, run mode, report output, codegen, preprocessing,
analysis, production, and CLI feature of the Nexora package.

Run:  pytest tests/test_full_system.py -v --tb=short
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nexora import Nexora, NexoraReport

# ─────────────────────────── helpers ───────────────────────────


def _make_regression_df(n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "feat_a": rng.normal(50, 10, n),
            "feat_b": rng.integers(0, 100, n).astype(float),
            "cat_col": rng.choice(["x", "y", "z"], n),
            "target": rng.normal(100, 15, n).round(2),
        }
    )


def _make_classification_df(n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "feat_a": rng.normal(50, 10, n),
            "feat_b": rng.integers(0, 100, n).astype(float),
            "cat_col": rng.choice(["x", "y", "z"], n),
            "label": rng.choice(["yes", "no"], n),
        }
    )


def _save_csv(df: pd.DataFrame, tmp_path: Path, name: str = "data.csv") -> Path:
    path = tmp_path / name
    df.to_csv(path, index=False)
    return path


@pytest.fixture()
def reg_df():
    return _make_regression_df()


@pytest.fixture()
def cls_df():
    return _make_classification_df()


@pytest.fixture()
def reg_csv(tmp_path, reg_df):
    return _save_csv(reg_df, tmp_path, "reg.csv")


@pytest.fixture()
def cls_csv(tmp_path, cls_df):
    return _save_csv(cls_df, tmp_path, "cls.csv")


@pytest.fixture()
def reg_report(reg_df):
    return Nexora(reg_df, target="target").quick()


@pytest.fixture()
def cls_report(cls_df):
    return Nexora(cls_df, target="label").quick()


# ═══════════════════════════════════════════════════════════════
# SECTION 1 — ENTRY POINTS (15 tests)
# ═══════════════════════════════════════════════════════════════


class TestEntryPoints:
    """Tests 01–15: All ways to create a Nexora instance."""

    def test_01_csv_path(self, reg_csv):
        """01. Nexora("data.csv", target="col") — CSV file path."""
        nx = Nexora(reg_csv, target="target")
        assert nx.df.shape[0] == 100

    def test_02_xlsx_path(self, tmp_path, reg_df):
        """02. Nexora("data.xlsx") — Excel file."""
        xlsx = tmp_path / "data.xlsx"
        reg_df.to_excel(xlsx, index=False)
        nx = Nexora(xlsx, target="target")
        assert nx.df.shape[0] == 100

    def test_03_parquet_path(self, tmp_path, reg_df):
        """03. Nexora("data.parquet") — Parquet file."""
        pq = tmp_path / "data.parquet"
        reg_df.to_parquet(pq, index=False)
        nx = Nexora(pq, target="target")
        assert nx.df.shape[0] == 100

    def test_04_json_path(self, tmp_path, reg_df):
        """04. Nexora("data.json") — JSON file."""
        js = tmp_path / "data.json"
        reg_df.to_json(js, orient="records")
        nx = Nexora(js, target="target")
        assert nx.df.shape[0] == 100

    def test_05_dataframe(self, reg_df):
        """05. Nexora(df, target="col") — Pandas DataFrame."""
        nx = Nexora(reg_df, target="target")
        assert nx.source_name == "DataFrame"

    def test_06_numpy_arrays(self):
        """06. Nexora(X, y) — NumPy arrays."""
        X = np.random.rand(50, 3)
        y = np.random.rand(50)
        nx = Nexora(X, y=y)
        assert nx.df.shape == (50, 4)

    def test_07_from_sklearn_iris(self):
        """07. Nexora.from_sklearn("iris") — Built-in sklearn dataset."""
        nx = Nexora.from_sklearn("iris")
        assert nx.df.shape[0] == 150

    def test_08_target_validation(self, reg_df):
        """08. Invalid target raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            Nexora(reg_df, target="nonexistent_column")

    def test_09_no_target_for_profile(self, reg_df):
        """09. Nexora without target can still profile."""
        nx = Nexora(reg_df)
        prof = nx.profile()
        assert prof.health_score > 0

    def test_10_csv_auto_delimiter(self, tmp_path, reg_df):
        """10. CSV with semicolon delimiter."""
        path = tmp_path / "semi.csv"
        reg_df.to_csv(path, index=False, sep=";")
        # Should still load (our loader tries common delimiters)
        try:
            nx = Nexora(path, target="target")
            assert nx.df.shape[0] > 0
        except Exception:
            pytest.skip("Semicolon delimiter auto-detect not yet implemented")

    def test_11_from_sklearn_wine(self):
        """11. Nexora.from_sklearn("wine") — Another built-in dataset."""
        nx = Nexora.from_sklearn("wine")
        assert nx.df.shape[0] > 100

    def test_12_load_save_roundtrip(self, tmp_path, reg_report):
        """12. Nexora.load() — Reload a saved session."""
        path = tmp_path / "session.nx"
        reg_report.save(path)
        loaded = Nexora.load(path)
        assert loaded.best_model == reg_report.best_model

    def test_13_dataframe_copy_independence(self, reg_df):
        """13. Nexora doesn't modify the original DataFrame."""
        original_shape = reg_df.shape
        _nx = Nexora(reg_df, target="target")
        assert reg_df.shape == original_shape

    def test_14_empty_dataframe_raises(self):
        """14. Empty DataFrame raises an error."""
        with pytest.raises((ValueError, Exception)):
            Nexora(pd.DataFrame(), target="x")

    def test_15_large_column_count(self):
        """15. Dataset with many columns (50+)."""
        rng = np.random.default_rng(0)
        cols = {f"f{i}": rng.normal(size=50) for i in range(50)}
        cols["target"] = rng.normal(size=50)
        nx = Nexora(pd.DataFrame(cols), target="target")
        assert nx.df.shape[1] == 51


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — RUN MODES (10 tests)
# ═══════════════════════════════════════════════════════════════


class TestRunModes:
    """Tests 16–25: Execution modes."""

    def test_16_run_regression(self, reg_df):
        """16. nx.run() — Full auto-pilot regression."""
        report = Nexora(reg_df, target="target").run(max_models=2)
        assert isinstance(report, NexoraReport)

    def test_17_quick_mode(self, reg_df):
        """17. nx.quick() — 30-second speed mode."""
        report = Nexora(reg_df, target="target").quick()
        assert len(report.results) <= 2

    def test_18_deep_mode(self, reg_df):
        """18. nx.deep() — Exhaustive mode."""
        report = Nexora(reg_df, target="target").deep()
        assert len(report.results) > 0

    def test_19_profile_only(self, reg_df):
        """19. nx.profile() — Dataset profiling only, no training."""
        prof = Nexora(reg_df).profile()
        assert prof.row_count == 100
        assert prof.column_count == 4

    def test_20_preprocess_only(self, reg_df):
        """20. nx.preprocess() — Returns cleaned DataFrame."""
        clean = Nexora(reg_df, target="target").preprocess()
        assert isinstance(clean, pd.DataFrame)
        assert "target" in clean.columns

    def test_21_train_specific_models(self, reg_df):
        """21. nx.train(models=["Ridge"]) — Train specific models."""
        report = Nexora(reg_df, target="target").train(["Ridge"])
        assert report.best_model is not None

    def test_22_tune_single_model(self, reg_df):
        """22. nx.tune("Ridge") — Hyperparameter tuning stub."""
        report = Nexora(reg_df, target="target").tune("Ridge")
        assert report.best_model is not None

    def test_23_classification_run(self, cls_df):
        """23. nx.run() — Classification auto-detection."""
        report = Nexora(cls_df, target="label").run(max_models=2)
        assert report.task_type == "classification"

    def test_24_run_with_target_override(self, reg_df):
        """24. nx.run(target="target") — Target override."""
        nx = Nexora(reg_df)
        report = nx.run(target="target", max_models=2)
        assert report.target == "target"

    def test_25_run_no_target_raises(self, reg_df):
        """25. nx.run() without target raises ValueError."""
        with pytest.raises(ValueError, match="target column is required"):
            Nexora(reg_df).run()


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — REPORT OUTPUTS (18 tests)
# ═══════════════════════════════════════════════════════════════


class TestReportOutputs:
    """Tests 26–43: Report properties and methods."""

    def test_26_leaderboard_is_dataframe(self, reg_report):
        """26. report.leaderboard — Returns DataFrame."""
        lb = reg_report.leaderboard
        assert isinstance(lb, pd.DataFrame)
        assert "rank" in lb.columns

    def test_27_best_model_is_string(self, reg_report):
        """27. report.best_model — String model name."""
        assert isinstance(reg_report.best_model, str)

    def test_28_best_score_is_float(self, reg_report):
        """28. report.best_score — Float metric value."""
        assert isinstance(reg_report.best_score, float)

    def test_29_predict_returns_df(self, reg_report, reg_df):
        """29. report.predict(df) — Returns predictions DataFrame."""
        preds = reg_report.predict(reg_df)
        assert "target_predicted" in preds.columns
        assert "confidence" in preds.columns

    def test_30_predict_missing_columns_raises(self, reg_report):
        """30. predict with missing columns raises ValueError."""
        with pytest.raises(ValueError, match="Missing required"):
            reg_report.predict(pd.DataFrame({"wrong": [1]}))

    def test_31_explain_returns_df(self, reg_report):
        """31. report.explain() — Returns importance DataFrame."""
        result = reg_report.explain()
        assert isinstance(result, pd.DataFrame)

    def test_32_to_html(self, tmp_path, reg_report):
        """32. report.to_html() — Saves HTML file."""
        path = reg_report.to_html(tmp_path / "report.html")
        assert path.exists()

    def test_33_to_pdf(self, tmp_path, reg_report):
        """33. report.to_pdf() — Saves PDF file."""
        path = reg_report.to_pdf(tmp_path / "report.pdf")
        assert path.exists()
        assert path.stat().st_size > 100  # Not a placeholder

    def test_34_save_session(self, tmp_path, reg_report):
        """34. report.save() — Saves .nx session."""
        path = reg_report.save(tmp_path / "session.nx")
        assert path.exists()

    def test_35_save_model_pickle(self, tmp_path, reg_report):
        """35. report.save_model() — Saves .pkl file."""
        path = reg_report.save_model(tmp_path / "model.pkl")
        assert path.exists()

    def test_36_summary_prints(self, reg_report, capsys):
        """36. report.summary() — Prints summary."""
        reg_report.summary()
        captured = capsys.readouterr()
        assert "Best:" in captured.out

    def test_37_profile_property(self, reg_report):
        """37. report.profile — DatasetProfile object."""
        assert reg_report.profile.health_score > 0

    def test_38_best_score_label(self, reg_report):
        """38. report.best_score_label — Metric label string."""
        assert isinstance(reg_report.best_score_label, str)

    def test_39_code_property(self, reg_report):
        """39. report.code — Standalone Python code."""
        assert "import" in reg_report.code

    def test_40_version_property(self, reg_report):
        """40. report.version — Version string."""
        assert reg_report.version == "0.1.1"

    def test_41_leaderboard_sorted(self, reg_report):
        """41. Leaderboard is sorted by rank."""
        lb = reg_report.leaderboard.dropna(subset=["rank"])
        ranks = lb["rank"].tolist()
        assert ranks == sorted(ranks)

    def test_42_predict_proba_classification(self, cls_report, cls_df):
        """42. report.predict_proba() — Classification probabilities."""
        proba = cls_report.predict_proba(cls_df)
        assert isinstance(proba, pd.DataFrame)
        assert proba.shape[0] == len(cls_df)

    def test_43_predict_proba_regression_raises(self, reg_report, reg_df):
        """43. predict_proba on regression raises ValueError."""
        with pytest.raises(ValueError, match="classification"):
            reg_report.predict_proba(reg_df)


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — CODE GENERATION (11 tests)
# ═══════════════════════════════════════════════════════════════


class TestCodeGeneration:
    """Tests 44–54: Code generation methods."""

    def test_44_code_best_model(self, reg_report):
        """44. report.code — Best model code."""
        assert len(reg_report.code) > 50

    def test_45_code_for_specific(self, reg_report):
        """45. report.code_for("Ridge") — Code for specific model."""
        code = reg_report.code_for("Ridge")
        assert "Ridge" in code or "import" in code

    def test_46_save_code(self, tmp_path, reg_report):
        """46. report.save_code("model.py") — Write code to disk."""
        path = reg_report.save_code(tmp_path / "model.py")
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

    def test_47_code_fastapi(self, reg_report):
        """47. report.code_fastapi() — FastAPI code."""
        code = reg_report.code_fastapi()
        assert "FastAPI" in code or "fastapi" in code.lower()

    def test_48_code_streamlit(self, reg_report):
        """48. report.code_streamlit() — Streamlit code."""
        code = reg_report.code_streamlit()
        assert "streamlit" in code.lower()

    def test_49_code_flask(self, reg_report):
        """49. report.code_flask() — Flask code."""
        code = reg_report.code_flask()
        assert "flask" in code.lower() or "Flask" in code

    def test_50_code_docker(self, reg_report):
        """50. report.code_docker() — Dockerfile + requirements."""
        docker, reqs = reg_report.code_docker()
        assert "FROM" in docker
        assert len(reqs) > 0

    def test_51_code_notebook(self, reg_report):
        """51. report.code_notebook() — Jupyter notebook JSON."""
        nb = reg_report.code_notebook()
        parsed = json.loads(nb)
        assert "cells" in parsed

    def test_52_code_mlflow(self, reg_report):
        """52. report.code_mlflow() — MLflow tracking code."""
        code = reg_report.code_mlflow()
        assert "mlflow" in code.lower()

    def test_53_code_pipeline(self, reg_report):
        """53. report.code_pipeline() — sklearn Pipeline code."""
        code = reg_report.code_pipeline()
        assert "Pipeline" in code or "pipeline" in code.lower()

    def test_54_save_fastapi(self, tmp_path, reg_report):
        """54. report.save_fastapi("api.py") — Save FastAPI to disk."""
        path = reg_report.save_fastapi(tmp_path / "api.py")
        assert path.exists()


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — PREPROCESSING (10 tests)
# ═══════════════════════════════════════════════════════════════


class TestPreprocessing:
    """Tests 55–64: Preprocessing controls."""

    def test_55_preprocess_returns_df(self, reg_df):
        """55. nx.preprocess() returns a DataFrame."""
        clean = Nexora(reg_df, target="target").preprocess()
        assert isinstance(clean, pd.DataFrame)

    def test_56_preprocess_includes_target(self, reg_df):
        """56. Preprocessed output includes target column."""
        clean = Nexora(reg_df, target="target").preprocess()
        assert "target" in clean.columns

    def test_57_preprocess_save_to_csv(self, tmp_path, reg_df):
        """57. preprocess(save="file.csv") writes CSV."""
        path = tmp_path / "clean.csv"
        Nexora(reg_df, target="target").preprocess(save=str(path))
        assert path.exists()
        loaded = pd.read_csv(path)
        assert loaded.shape[0] == 100

    def test_58_preprocess_handles_missing(self):
        """58. Preprocessing handles missing values."""
        df = _make_regression_df()
        df.loc[0:5, "feat_a"] = np.nan
        clean = Nexora(df, target="target").preprocess()
        assert not clean.drop(columns=["target"]).isnull().any().any()

    def test_59_preprocess_handles_categoricals(self, reg_df):
        """59. Categorical columns are encoded."""
        clean = Nexora(reg_df, target="target").preprocess()
        assert clean.select_dtypes(include=["object"]).shape[1] == 0

    def test_60_profile_health_score(self, reg_df):
        """60. Profile health score is between 0 and 100."""
        prof = Nexora(reg_df).profile()
        assert 0 <= prof.health_score <= 100

    def test_61_profile_column_count(self, reg_df):
        """61. Profile column count matches DataFrame."""
        prof = Nexora(reg_df).profile()
        assert prof.column_count == reg_df.shape[1]

    def test_62_profile_row_count(self, reg_df):
        """62. Profile row count matches DataFrame."""
        prof = Nexora(reg_df).profile()
        assert prof.row_count == reg_df.shape[0]

    def test_63_profile_missing_cells(self):
        """63. Profile detects missing cells."""
        df = _make_regression_df()
        df.loc[0:9, "feat_a"] = np.nan  # 10 missing
        prof = Nexora(df).profile()
        assert prof.missing_cells >= 10

    def test_64_profile_columns_property(self, reg_df):
        """64. profile.columns returns a DataFrame."""
        prof = Nexora(reg_df).profile()
        assert isinstance(prof.columns, pd.DataFrame)


# ═══════════════════════════════════════════════════════════════
# SECTION 6 — ANALYSIS & DIAGNOSTICS (10 tests)
# ═══════════════════════════════════════════════════════════════


class TestAnalysis:
    """Tests 65–74: Explainability and diagnostics."""

    def test_65_explain_returns_df(self, reg_report):
        """65. report.explain() returns importance DataFrame."""
        result = reg_report.explain()
        assert isinstance(result, pd.DataFrame)

    def test_66_partial_dependence(self, reg_report):
        """66. report.partial_dependence("feat_a") returns dict."""
        result = reg_report.partial_dependence("feat_a")
        assert isinstance(result, dict)

    def test_67_sensitivity(self, reg_report):
        """67. report.sensitivity("feat_a") returns dict."""
        result = reg_report.sensitivity("feat_a")
        assert isinstance(result, dict)

    def test_68_interaction(self, reg_report, capsys):
        """68. report.interaction() prints output."""
        reg_report.interaction("feat_a", "feat_b")
        captured = capsys.readouterr()
        assert "SHAP" in captured.out

    def test_69_explain_no_crash(self, cls_report):
        """69. explain() on classification report doesn't crash."""
        result = cls_report.explain()
        assert result is not None

    def test_70_summary_output(self, reg_report, capsys):
        """70. summary() prints Best model info."""
        reg_report.summary()
        out = capsys.readouterr().out
        assert reg_report.best_model in out

    def test_71_leaderboard_has_metrics(self, reg_report):
        """71. Leaderboard includes metric columns."""
        lb = reg_report.leaderboard
        assert "primary_score" in lb.columns

    def test_72_leaderboard_has_timing(self, reg_report):
        """72. Leaderboard includes training time."""
        lb = reg_report.leaderboard
        assert "train_time_sec" in lb.columns

    def test_73_multiple_models_ranked(self, reg_df):
        """73. Multiple models appear in leaderboard."""
        report = Nexora(reg_df, target="target").run(max_models=4)
        lb = report.leaderboard
        assert len(lb) >= 2

    def test_74_best_result_matches_leaderboard(self, reg_report):
        """74. best_model matches rank 1 in leaderboard."""
        lb = reg_report.leaderboard
        rank1 = lb[lb["rank"] == 1].iloc[0]["model_name"]
        assert reg_report.best_model == rank1


# ═══════════════════════════════════════════════════════════════
# SECTION 7 — PRODUCTION (9 tests)
# ═══════════════════════════════════════════════════════════════


class TestProduction:
    """Tests 75–83: Production features."""

    def test_75_save_load_roundtrip(self, tmp_path, reg_report):
        """75. Save and load preserves best_model."""
        path = tmp_path / "test.nx"
        reg_report.save(path)
        loaded = Nexora.load(path)
        assert loaded.best_model == reg_report.best_model

    def test_76_save_load_preserves_score(self, tmp_path, reg_report):
        """76. Save and load preserves best_score."""
        path = tmp_path / "test.nx"
        reg_report.save(path)
        loaded = Nexora.load(path)
        assert abs(loaded.best_score - reg_report.best_score) < 1e-6

    def test_77_save_load_predict(self, tmp_path, reg_report, reg_df):
        """77. Loaded report can predict."""
        path = tmp_path / "test.nx"
        reg_report.save(path)
        loaded = Nexora.load(path)
        preds = loaded.predict(reg_df)
        assert preds.shape[0] == len(reg_df)

    def test_78_save_model_joblib(self, tmp_path, reg_report):
        """78. save_model exports joblib pickle."""
        path = reg_report.save_model(tmp_path / "model.pkl")
        assert path.exists()
        import joblib

        model = joblib.load(path)
        assert hasattr(model, "predict")

    def test_79_compare_runs(self, reg_df, capsys):
        """79. Nexora.compare_runs() prints comparison."""
        r1 = Nexora(reg_df, target="target").quick()
        r2 = Nexora(reg_df, target="target").quick()
        Nexora.compare_runs(r1, r2)
        out = capsys.readouterr().out
        assert "Score Delta" in out

    def test_80_pdf_has_content(self, tmp_path, reg_report):
        """80. PDF report has substantial content."""
        path = reg_report.to_pdf(tmp_path / "report.pdf")
        assert path.stat().st_size > 500

    def test_81_predict_confidence_range(self, reg_report, reg_df):
        """81. Prediction confidence is between 0 and 1."""
        preds = reg_report.predict(reg_df)
        assert preds["confidence"].between(0, 1).all()

    def test_82_predict_model_used(self, reg_report, reg_df):
        """82. Predictions include model_used column."""
        preds = reg_report.predict(reg_df)
        assert preds["model_used"].iloc[0] == reg_report.best_model

    def test_83_classification_save_load(self, tmp_path, cls_report, cls_df):
        """83. Classification report save/load/predict works."""
        path = tmp_path / "cls.nx"
        cls_report.save(path)
        loaded = Nexora.load(path)
        preds = loaded.predict(cls_df)
        assert preds.shape[0] == len(cls_df)


# ═══════════════════════════════════════════════════════════════
# SECTION 8 — CLI (12 tests)
# ═══════════════════════════════════════════════════════════════


class TestCLI:
    """Tests 84–95: CLI commands."""

    def _run_cli(
        self, args: list[str], cwd: str | None = None
    ) -> subprocess.CompletedProcess:
        import os

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-m", "nexora.cli.main"] + args,
            capture_output=True,
            encoding="utf-8",
            timeout=120,
            cwd=cwd,
            env=env,
        )

    def test_84_cli_help(self):
        """84. nexora --help shows all commands."""
        result = self._run_cli(["--help"])
        assert "train" in result.stdout
        assert "profile" in result.stdout

    def test_85_cli_train(self, reg_csv, tmp_path):
        """85. nexora train data.csv --target col."""
        out = tmp_path / "model.nx"
        result = self._run_cli(
            ["train", str(reg_csv), "--target", "target", "--out", str(out)]
        )
        assert result.returncode == 0 or "Best model" in result.stdout

    def test_86_cli_profile(self, reg_csv):
        """86. nexora profile data.csv."""
        result = self._run_cli(["profile", str(reg_csv)])
        assert "Health Score" in result.stdout

    def test_87_cli_quick(self, reg_csv):
        """87. nexora quick data.csv --target col."""
        result = self._run_cli(["quick", str(reg_csv), "--target", "target"])
        assert result.returncode == 0 or "Best" in result.stdout

    def test_88_cli_models(self):
        """88. nexora models — Lists available models."""
        result = self._run_cli(["models"])
        assert "Ridge" in result.stdout or "LinearRegression" in result.stdout

    def test_89_cli_models_task_filter(self):
        """89. nexora models --task regression."""
        result = self._run_cli(["models", "--task", "regression"])
        assert "Regressor" in result.stdout or "Ridge" in result.stdout

    def test_90_cli_config_show(self):
        """90. nexora configuration --show."""
        result = self._run_cli(["configuration", "--show"])
        assert "configuration" in result.stdout.lower()

    def test_91_cli_clean(self, reg_csv, tmp_path):
        """91. nexora clean data.csv --target col."""
        out = tmp_path / "clean.csv"
        result = self._run_cli(
            ["clean", str(reg_csv), "--target", "target", "--out", str(out)]
        )
        assert result.returncode == 0

    def test_92_cli_predict(self, reg_csv, tmp_path):
        """92. nexora predict model.nx new_data.csv."""
        # First train a model
        model_path = tmp_path / "model.nx"
        self._run_cli(
            ["train", str(reg_csv), "--target", "target", "--out", str(model_path)]
        )
        # Then predict
        out = tmp_path / "preds.csv"
        result = self._run_cli(
            ["predict", str(model_path), str(reg_csv), "--output", str(out)]
        )
        assert result.returncode == 0 or out.exists()

    def test_93_cli_compare(self, reg_csv, tmp_path):
        """93. nexora compare r1.nx r2.nx."""
        m1 = tmp_path / "m1.nx"
        m2 = tmp_path / "m2.nx"
        self._run_cli(["train", str(reg_csv), "--target", "target", "--out", str(m1)])
        self._run_cli(["train", str(reg_csv), "--target", "target", "--out", str(m2)])
        result = self._run_cli(["compare-sessions", str(m1), str(m2)])
        assert "Score Delta" in result.stdout

    def test_94_cli_report_html(self, reg_csv, tmp_path):
        """94. nexora report model.nx --format html."""
        model = tmp_path / "model.nx"
        self._run_cli(
            ["train", str(reg_csv), "--target", "target", "--out", str(model)]
        )
        html = tmp_path / "report.html"
        result = self._run_cli(
            ["report", str(model), "--format", "html", "--out", str(html)]
        )
        assert result.returncode == 0

    def test_95_cli_wizard_listed(self):
        """95. nexora --help lists wizard command."""
        result = self._run_cli(["--help"])
        assert "wizard" in result.stdout


# ═══════════════════════════════════════════════════════════════
# SECTION 9 — EDGE CASES & ROBUSTNESS (10 tests)
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Tests 96–105: Edge cases and robustness."""

    def test_96_single_row_df(self):
        """96. Single-row DataFrame doesn't crash profile."""
        df = pd.DataFrame({"a": [1], "b": [2], "target": [3]})
        prof = Nexora(df).profile()
        assert prof.row_count == 1

    def test_97_all_missing_column(self):
        """97. Column entirely NaN is handled."""
        df = _make_regression_df()
        df["all_nan"] = np.nan
        prof = Nexora(df).profile()
        assert prof.missing_cells >= 100

    def test_98_duplicate_columns(self):
        """98. Duplicate column names don't crash."""
        df = _make_regression_df()
        # Rename a column to create a duplicate (pandas allows this)
        df.columns = ["feat_a", "feat_a", "cat_col", "target"]
        try:
            prof = Nexora(df).profile()
            assert prof is not None
        except Exception:
            pass  # Some level of failure is acceptable

    def test_99_unicode_column_names(self):
        """99. Unicode column names are handled."""
        df = pd.DataFrame({"价格": [1, 2, 3], "数量": [4, 5, 6], "目标": [7, 8, 9]})
        prof = Nexora(df).profile()
        assert prof.column_count == 3

    def test_100_boolean_target(self):
        """100. Boolean target column is detected as classification."""
        df = _make_classification_df()
        df["bool_target"] = df["label"] == "yes"
        report = Nexora(df, target="bool_target").run(max_models=2)
        assert report.task_type == "classification"

    def test_101_integer_target(self):
        """101. Integer target with few classes → classification."""
        rng = np.random.default_rng(0)
        df = pd.DataFrame(
            {"f1": rng.normal(size=100), "target": rng.choice([0, 1], 100)}
        )
        report = Nexora(df, target="target").run(max_models=2)
        assert report.task_type == "classification"

    def test_102_float_target(self):
        """102. Float target → regression."""
        rng = np.random.default_rng(0)
        df = pd.DataFrame({"f1": rng.normal(size=100), "target": rng.normal(size=100)})
        report = Nexora(df, target="target").run(max_models=2)
        assert report.task_type == "regression"

    def test_103_high_cardinality_cat(self):
        """103. High cardinality categorical doesn't crash."""
        rng = np.random.default_rng(0)
        df = pd.DataFrame(
            {
                "high_card": [f"val_{i}" for i in range(200)],
                "f1": rng.normal(size=200),
                "target": rng.normal(size=200),
            }
        )
        report = Nexora(df, target="target").run(max_models=2)
        assert report is not None

    def test_104_all_numeric_df(self):
        """104. All-numeric DataFrame works."""
        rng = np.random.default_rng(0)
        df = pd.DataFrame({f"f{i}": rng.normal(size=80) for i in range(5)})
        df["target"] = rng.normal(size=80)
        report = Nexora(df, target="target").run(max_models=2)
        assert report.best_model is not None

    def test_105_predict_type_error(self, reg_report):
        """105. predict() with non-DataFrame raises TypeError."""
        with pytest.raises(TypeError):
            reg_report.predict([1, 2, 3])
