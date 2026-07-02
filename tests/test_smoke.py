"""
Nexora Smoke Tests
==================
Quick sanity checks that can run in < 30 seconds.
Verifies the critical path: import → load → profile → train → predict → save.

Run: pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nexora import Nexora, NexoraReport, __version__

# ───────── fixtures ─────────


@pytest.fixture(scope="module")
def sample_df():
    rng = np.random.default_rng(42)
    n = 80
    return pd.DataFrame(
        {
            "price": rng.uniform(10, 500, n).round(2),
            "quantity": rng.integers(1, 50, n),
            "category": rng.choice(["electronics", "clothing", "food"], n),
            "revenue": (rng.uniform(100, 5000, n)).round(2),
        }
    )


@pytest.fixture(scope="module")
def trained_report(sample_df):
    return Nexora(sample_df, target="revenue").quick()


# ───────── smoke tests ─────────


class TestSmoke:
    """Quick sanity checks for the critical path."""

    def test_import(self):
        """Package imports without errors."""
        assert Nexora is not None
        assert NexoraReport is not None
        assert __version__ == "0.1.2"

    def test_create_instance(self, sample_df):
        """Can create a Nexora instance from DataFrame."""
        nx = Nexora(sample_df, target="revenue")
        assert nx.df.shape[0] == 80

    def test_profile(self, sample_df):
        """Profile runs without errors."""
        prof = Nexora(sample_df).profile()
        assert prof.health_score > 0
        assert prof.row_count == 80

    def test_quick_train(self, trained_report):
        """Quick training completes and returns a report."""
        assert isinstance(trained_report, NexoraReport)
        assert trained_report.best_model is not None
        assert isinstance(trained_report.best_score, float)

    def test_leaderboard(self, trained_report):
        """Leaderboard is a valid DataFrame."""
        lb = trained_report.leaderboard
        assert isinstance(lb, pd.DataFrame)
        assert len(lb) >= 1

    def test_predict(self, trained_report, sample_df):
        """Predictions return valid DataFrame."""
        preds = trained_report.predict(sample_df)
        assert "revenue_predicted" in preds.columns
        assert len(preds) == len(sample_df)

    def test_code_gen(self, trained_report):
        """Code generation produces non-empty string."""
        code = trained_report.code
        assert isinstance(code, str)
        assert len(code) > 50

    def test_explain(self, trained_report):
        """Explain runs without crashing."""
        result = trained_report.explain()
        assert result is not None

    def test_save_load(self, tmp_path, trained_report, sample_df):
        """Save and load preserves predictions."""
        path = tmp_path / "smoke.nx"
        trained_report.save(path)
        loaded = Nexora.load(path)
        preds_original = trained_report.predict(sample_df)
        preds_loaded = loaded.predict(sample_df)
        pd.testing.assert_frame_equal(preds_original, preds_loaded)

    def test_pdf_generation(self, tmp_path, trained_report):
        """PDF generation produces a file."""
        path = trained_report.to_pdf(tmp_path / "smoke.pdf")
        assert path.exists()
        assert path.stat().st_size > 100

    def test_from_sklearn(self):
        """from_sklearn loads iris dataset."""
        nx = Nexora.from_sklearn("iris")
        assert nx.df.shape[0] == 150
