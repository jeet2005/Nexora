"""SHAP-based model explainability engine for Phase 4."""

from __future__ import annotations

import base64
import io
import warnings
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from app.config import settings
from app.services.model_registry import ModelSpec, get_models_for_problem

matplotlib.use("Agg")


warnings.filterwarnings("ignore")

plt.style.use("default")

PLOT_DPI = 120
MAX_FEATURES_SHAP = 15
PLOT_BG = "#ffffff"
TEXT = "#202124"
MUTED = "#5f6368"
GRID = "#e8eaed"
GOOGLE_COLORS = ["#4285f4", "#34a853",
                 "#fbbc05", "#ea4335", "#a142f4", "#00acc1"]


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=PLOT_DPI,
        bbox_inches="tight",
        facecolor=PLOT_BG,
        edgecolor="none",
        transparent=False,
    )
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def _get_best_model_spec(problem_type: str, model_id: str) -> ModelSpec | None:
    """Look up the ModelSpec by ID from the registry."""
    for spec in get_models_for_problem(problem_type):
        if spec.id == model_id:
            return spec
    return None


def _train_model(spec: ModelSpec, X_train: np.ndarray, y_train: np.ndarray):
    """Build a trained model from a spec."""
    model = spec.factory()
    model.fit(X_train, y_train)
    return model


def _prepare_xy(
    df: pd.DataFrame, target_column: str
) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """Build a numeric feature matrix so SHAP never receives object arrays."""
    feature_cols = [c for c in df.columns if c != target_column]
    X = df[feature_cols].copy()

    for col in X.columns:
        if pd.api.types.is_bool_dtype(X[col]):
            X[col] = X[col].astype(int)
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce")

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)
    X = X.astype(np.float64)
    return X, df[target_column].values, list(X.columns)


def _compute_shap_values(
    model,
    X_train: np.ndarray,
    X_test: np.ndarray,
    feature_names: list[str],
    problem_type: str,
) -> tuple[shap.Explanation | np.ndarray, Any]:
    """Compute SHAP values using the best available explainer."""
    # Sample for speed
    bg_size = min(100, len(X_train))
    bg = X_train[np.random.choice(len(X_train), bg_size, replace=False)]
    explain_size = min(200, len(X_test))
    X_explain = X_test[:explain_size]

    model_type = type(model).__name__.lower()
    tree_types = (
        "forest",
        "tree",
        "gradient",
        "xgb",
        "lgbm",
        "catboost",
        "hist",
        "extra",
        "ada",
        "bagging",
    )

    try:
        if any(t in model_type for t in tree_types):
            explainer = shap.TreeExplainer(model)
            sv = explainer(X_explain)
        else:
            explainer = shap.KernelExplainer(model.predict, bg)
            raw_sv = explainer.shap_values(X_explain)
            sv = shap.Explanation(
                values=raw_sv,
                base_values=np.full(len(X_explain), explainer.expected_value),
                data=X_explain,
                feature_names=feature_names,
            )
    except Exception:
        # Fallback to permutation explainer
        explainer = shap.Explainer(model.predict, bg)
        sv = explainer(X_explain)

    # Ensure feature_names are set
    if hasattr(sv, "feature_names") and sv.feature_names is None:
        sv.feature_names = feature_names

    return sv, explainer


def _plot_shap_summary(sv: shap.Explanation, feature_names: list[str]) -> str:
    """Create a SHAP beeswarm/summary plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(
        sv, feature_names=feature_names, show=False, max_display=MAX_FEATURES_SHAP
    )
    ax = plt.gca()
    ax.set_facecolor(PLOT_BG)
    fig.patch.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.set_title(
        "SHAP Feature Impact", color=TEXT, fontsize=14, fontweight="bold", pad=12
    )
    return _fig_to_base64(fig)


def _plot_shap_bar(sv: shap.Explanation, feature_names: list[str]) -> str:
    """Create a SHAP bar chart of mean absolute SHAP values."""
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.plots.bar(sv, show=False, max_display=MAX_FEATURES_SHAP)
    ax = plt.gca()
    ax.set_facecolor(PLOT_BG)
    fig.patch.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.set_title(
        "Feature Importance (mean |SHAP|)",
        color=TEXT,
        fontsize=14,
        fontweight="bold",
        pad=12,
    )
    return _fig_to_base64(fig)


def _compute_feature_importance(
    sv: shap.Explanation, feature_names: list[str]
) -> list[dict]:
    """Extract ranked feature importance from SHAP values."""
    if hasattr(sv, "values"):
        vals = sv.values
    else:
        vals = np.array(sv)

    if vals.ndim == 3:
        # Multi-output: take the first output (or mean across outputs)
        vals = vals[:, :, 0]

    mean_abs = np.abs(vals).mean(axis=0)
    if len(mean_abs) != len(feature_names):
        feature_names = [f"Feature {i}" for i in range(len(mean_abs))]

    ranked = sorted(
        zip(feature_names, mean_abs.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )
    total = sum(v for _, v in ranked) or 1
    return [
        {
            "feature": name,
            "importance": round(float(val), 6),
            "percentage": round(float(val) / total * 100, 2),
        }
        for name, val in ranked[:MAX_FEATURES_SHAP]
    ]


def _plot_feature_importance_bar(importances: list[dict]) -> str:
    """Create a styled horizontal bar chart of feature importance."""
    names = [d["feature"] for d in importances[:12]][::-1]
    vals = [d["importance"] for d in importances[:12]][::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [GOOGLE_COLORS[i % len(GOOGLE_COLORS)] for i in range(len(names))]
    bars = ax.barh(names, vals, color=colors, height=0.6, edgecolor="none")

    ax.set_facecolor(PLOT_BG)
    fig.patch.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=10)
    ax.xaxis.label.set_color(MUTED)
    ax.set_xlabel("Importance", fontsize=11, color=MUTED)
    ax.set_title(
        "Top Feature Importance", color=TEXT, fontsize=14, fontweight="bold", pad=12
    )
    ax.grid(axis="x", alpha=0.8, color=GRID)

    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_width() + max(vals) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}",
            ha="left",
            va="center",
            color=MUTED,
            fontsize=9,
        )

    plt.tight_layout()
    return _fig_to_base64(fig)


def _plot_prediction_distribution(y_test, y_pred, problem_type: str) -> str:
    """Plot actual vs predicted distribution."""
    fig, ax = plt.subplots(figsize=(10, 6))

    if problem_type == "regression":
        ax.scatter(y_test, y_pred, alpha=0.72, s=18,
                   c="#4285f4", edgecolors="none")
        lims = [min(y_test.min(), y_pred.min()),
                max(y_test.max(), y_pred.max())]
        ax.plot(
            lims,
            lims,
            "--",
            color="#ea4335",
            alpha=0.8,
            linewidth=1.5,
            label="Perfect prediction",
        )
        ax.set_xlabel("Actual", color=MUTED, fontsize=11)
        ax.set_ylabel("Predicted", color=MUTED, fontsize=11)
        ax.set_title(
            "Actual vs Predicted", color=TEXT, fontsize=14, fontweight="bold", pad=12
        )
        ax.legend(facecolor=PLOT_BG, edgecolor=GRID, labelcolor=MUTED)
    else:
        import seaborn as sns
        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=ax,
            linewidths=0.5,
            linecolor=GRID,
            cbar_kws={"shrink": 0.8},
        )
        ax.set_xlabel("Predicted", color=MUTED, fontsize=11)
        ax.set_ylabel("Actual", color=MUTED, fontsize=11)
        ax.set_title(
            "Confusion Matrix", color=TEXT, fontsize=14, fontweight="bold", pad=12
        )
        ax.tick_params(colors=MUTED)

    ax.set_facecolor(PLOT_BG)
    fig.patch.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    plt.tight_layout()
    return _fig_to_base64(fig)


def _plot_residuals(y_test, y_pred) -> str:
    """Plot residuals for regression models."""
    residuals = y_test - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Residual scatter
    ax = axes[0]
    ax.scatter(y_pred, residuals, alpha=0.65, s=16,
               c="#a142f4", edgecolors="none")
    ax.axhline(0, color="#ea4335", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("Predicted", color=MUTED, fontsize=10)
    ax.set_ylabel("Residual", color=MUTED, fontsize=10)
    ax.set_title("Residual Plot", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)

    # Residual histogram
    ax = axes[1]
    ax.hist(residuals, bins=30, color="#34a853", alpha=0.78, edgecolor=PLOT_BG)
    ax.axvline(0, color="#ea4335", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xlabel("Residual", color=MUTED, fontsize=10)
    ax.set_ylabel("Frequency", color=MUTED, fontsize=10)
    ax.set_title("Residual Distribution", color=TEXT,
                 fontsize=12, fontweight="bold")
    ax.set_facecolor(PLOT_BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)

    fig.patch.set_facecolor(PLOT_BG)
    plt.tight_layout()
    return _fig_to_base64(fig)


def _fallback_feature_importance(
    model, X_test: np.ndarray, y_test: np.ndarray, feature_names: list[str]
) -> list[dict]:
    """Return feature importances without SHAP when SHAP cannot handle a model/data combo."""
    if hasattr(model, "feature_importances_"):
        raw = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "coef_"):
        raw = np.abs(np.asarray(model.coef_, dtype=float))
        if raw.ndim > 1:
            raw = raw.mean(axis=0)
    else:
        try:
            perm = permutation_importance(
                model,
                X_test,
                y_test,
                n_repeats=5,
                random_state=42,
                n_jobs=1,
            )
            raw = np.maximum(perm.importances_mean, 0)
        except Exception:
            raw = np.zeros(len(feature_names), dtype=float)

    if len(raw) != len(feature_names):
        raw = np.resize(raw, len(feature_names))

    total = float(np.sum(np.abs(raw))) or 1.0
    ranked = sorted(
        zip(feature_names, np.abs(raw)), key=lambda item: item[1], reverse=True
    )
    return [
        {
            "feature": name,
            "importance": round(float(val), 6),
            "percentage": round(float(val) / total * 100, 2),
        }
        for name, val in ranked[:MAX_FEATURES_SHAP]
    ]


def run_explainability(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    model_id: str,
) -> dict[str, Any]:
    """Run full explainability pipeline for the best model."""
    spec = _get_best_model_spec(problem_type, model_id)
    if not spec:
        raise ValueError(
            f"Model '{model_id}' not found in registry for {problem_type}."
        )

    X_df, y, feature_cols = _prepare_xy(df, target_column)
    X = X_df.values

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=settings.train_test_split,
        random_state=42,
    )

    # Train the specific model
    model = _train_model(spec, X_train, y_train)
    y_pred = model.predict(X_test)

    # Compute SHAP when possible. Some SHAP/Numba paths crash on object-like data;
    # fallback importances keep the feature usable instead of failing the request.
    sv = None
    try:
        sv, _ = _compute_shap_values(
            model, X_train, X_test, feature_cols, problem_type)
        importances = _compute_feature_importance(sv, feature_cols)
    except Exception:
        importances = _fallback_feature_importance(
            model, X_test, y_test, feature_cols)

    # Generate plots
    plots: dict[str, str] = {}
    if sv is not None:
        try:
            plots["shap_summary"] = _plot_shap_summary(sv, feature_cols)
        except Exception:
            pass
        try:
            plots["shap_bar"] = _plot_shap_bar(sv, feature_cols)
        except Exception:
            pass
    try:
        plots["feature_importance"] = _plot_feature_importance_bar(importances)
    except Exception:
        pass
    try:
        plots["prediction_distribution"] = _plot_prediction_distribution(
            y_test, y_pred, problem_type
        )
    except Exception:
        pass
    if problem_type == "regression":
        try:
            plots["residuals"] = _plot_residuals(y_test, y_pred)
        except Exception:
            pass

    # Model metrics
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        mean_absolute_error,
        mean_squared_error,
        r2_score,
        roc_auc_score,
    )

    metrics: dict[str, float] = {}
    if problem_type == "classification":
        metrics["accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4)
        metrics["f1"] = round(
            float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4
        )
        try:
            if hasattr(model, "predict_proba") and len(np.unique(y_test)) == 2:
                proba = model.predict_proba(X_test)[:, 1]
                metrics["roc_auc"] = round(
                    float(roc_auc_score(y_test, proba)), 4)
        except Exception:
            pass
    else:
        metrics["mae"] = round(float(mean_absolute_error(y_test, y_pred)), 4)
        metrics["rmse"] = round(
            float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)
        metrics["r2"] = round(float(r2_score(y_test, y_pred)), 4)

    return {
        "model_id": model_id,
        "model_name": spec.name,
        "family": spec.family,
        "problem_type": problem_type,
        "feature_importance": importances,
        "plots": plots,
        "metrics": metrics,
        "sample_count": len(X),
        "test_count": len(X_test),
        "feature_count": len(feature_cols),
    }
