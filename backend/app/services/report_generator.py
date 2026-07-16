"""PDF report generator for Nexora analytics — Phase 4."""

from __future__ import annotations

import base64
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

from app.config import settings


def _pdf_text(value: Any) -> str:
    """Keep report text compatible with built-in PDF fonts."""
    text = str(value)
    replacements = {
        "x": "x",
        "·": "-",
        "—": "-",
        "–": "-",
        "→": "->",
        "⚠": "!",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "‑": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


class NexoraReport(FPDF):
    """Custom PDF with Nexora branding."""

    BG = (250, 250, 249)  # #fafaf9 (nexora-bg)
    TEXT = (23, 21, 20)  # #171514 (nexora-dark)
    ACCENT = (147, 201, 152)  # #93C998 (nexora-accent)
    SECONDARY = (122, 179, 127)  # #7ab37f (nexora-accent-dark)
    MUTED = (120, 113, 108)  # #78716c (neutral warm gray)
    WHITE = (255, 255, 255)
    GREEN = (122, 179, 127)
    RED = (239, 68, 68)

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_fill_color(*self.BG)

    def header(self):
        self.set_fill_color(*self.BG)
        self.rect(0, 0, 210, 297, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.TEXT)
        self.cell(0, 8, "NEXORA AI", align="L")
        self.set_text_color(*self.MUTED)
        self.set_font("Helvetica", "", 7)
        self.cell(
            0,
            8,
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*self.MUTED)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.ln(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*self.TEXT)
        self.cell(0, 10, _pdf_text(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def sub_title(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.SECONDARY)
        self.cell(0, 8, _pdf_text(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT)
        self.multi_cell(0, 5, _pdf_text(text))
        self.ln(2)

    def metric_row(self, label: str, value: str, highlight: bool = False):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.MUTED)
        self.cell(60, 6, _pdf_text(label), new_x="END")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*(self.GREEN if highlight else self.TEXT))
        self.cell(0, 6, _pdf_text(value), new_x="LMARGIN", new_y="NEXT")

    def add_base64_image(self, b64_str: str, w: int = 180):
        """Insert a base64 PNG image into the PDF."""
        img_bytes = base64.b64decode(b64_str)
        # Write to temp file because FPDF needs a file path
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(img_bytes)
        tmp.close()
        try:
            if self.get_y() + 100 > 270:
                self.add_page()
            self.image(tmp.name, x=15, w=w)
            self.ln(6)
        finally:
            os.unlink(tmp.name)


def _generate_report(
    dataset_info: dict,
    training_result: dict,
    explainability: dict | None = None,
    insights: dict | None = None,
) -> bytes:
    """Generate a comprehensive PDF report and return as bytes."""
    pdf = NexoraReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Cover Title ──
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*NexoraReport.TEXT)
    pdf.cell(0, 14, "Predictive Analytics", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*NexoraReport.ACCENT)
    pdf.cell(0, 14, "Intelligence Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*NexoraReport.MUTED)
    pdf.cell(
        0,
        8,
        _pdf_text(f"Dataset: {dataset_info.get('filename', 'Unknown')}"),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(
        0,
        7,
        _pdf_text(
            f"{dataset_info.get('rows', 0):,} rows x {dataset_info.get('columns', 0)} columns"
        ),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(
        0,
        7,
        _pdf_text(
            f"Target: {dataset_info.get('target_column', 'N/A')} ({dataset_info.get('problem_type', 'N/A')})"
        ),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(10)

    pdf.set_draw_color(*NexoraReport.ACCENT)
    pdf.set_line_width(0.2)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*NexoraReport.MUTED)
    pdf.cell(
        0,
        6,
        "Powered by Nexora AI - Autonomous Predictive Analytics Platform",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    # ── Step-by-Step Guide (for beginners) ──
    pdf.add_page()
    pdf.section_title("Quick Start Guide")
    pdf.body_text(
        "Welcome! This report was generated automatically by Nexora AI. "
        "Here is a step-by-step breakdown of how Nexora analyzed your data "
        "and what each section of this report means."
    )

    guide_steps = [
        (
            "Step 1: Upload",
            "You uploaded a CSV/Excel file. Nexora instantly read your data, detected column types, found duplicates, and measured overall data quality.",
        ),
        (
            "Step 2: Target Selection",
            "You selected a target column to predict. Nexora auto-detected whether this is a Classification problem (predicting categories) or Regression (predicting numbers).",
        ),
        (
            "Step 3: Preprocessing",
            "Nexora cleaned your data automatically - handling missing values, encoding text columns to numbers, removing outliers, and scaling features for optimal ML performance.",
        ),
        (
            "Step 4: Model Arena",
            "100+ machine learning models competed on your data. Each model was trained and scored, then ranked on a leaderboard. The best-performing model became the Champion.",
        ),
        (
            "Step 5: SHAP Explainability",
            "SHAP analysis explains WHY the champion model makes its predictions. It shows which features matter most and how each feature pushes the prediction up or down.",
        ),
        (
            "Step 6: This Report",
            "Everything is compiled into this PDF - dataset stats, leaderboard, SHAP charts, and model metrics - so you can share results with your team.",
        ),
    ]

    for title, desc in guide_steps:
        pdf.sub_title(title)
        pdf.body_text(desc)

    pdf.ln(4)
    pdf.body_text(
        "Tip: Focus on the Champion Model section and SHAP Feature Importance to "
        "understand your prediction results. The leaderboard shows how other models "
        "compared."
    )

    # ── Dataset Overview ──
    pdf.add_page()
    pdf.section_title("1. Dataset Overview")
    pdf.metric_row("Filename", dataset_info.get("filename", "N/A"))
    pdf.metric_row("Rows", f"{dataset_info.get('rows', 0):,}")
    pdf.metric_row("Columns", str(dataset_info.get("columns", 0)))
    pdf.metric_row("Target Column", dataset_info.get("target_column", "N/A"))
    pdf.metric_row("Problem Type", dataset_info.get("problem_type", "N/A").title())
    pdf.metric_row("Duplicate Rows", str(dataset_info.get("duplicate_rows", 0)))
    pdf.metric_row("Memory", f"{dataset_info.get('memory_mb', 0)} MB")

    if insights:
        pdf.ln(4)
        pdf.sub_title("AI Narrative")
        pdf.body_text(insights.get("narrative", "No narrative available."))

        if insights.get("quality_warnings"):
            pdf.sub_title("Quality Warnings")
            for w in insights["quality_warnings"]:
                pdf.body_text(f"! {w}")

        pdf.metric_row(
            "Prediction Difficulty",
            f"{insights.get('estimated_difficulty', '?')} / 100",
        )

    # ── Training Results ──
    pdf.add_page()
    pdf.section_title("2. Model Training Results")
    pdf.metric_row("Models Attempted", str(training_result.get("total_attempted", 0)))
    pdf.metric_row(
        "Models Completed",
        str(training_result.get("total_completed", 0)),
        highlight=True,
    )
    pdf.metric_row("Models Failed", str(training_result.get("total_failed", 0)))
    pdf.metric_row(
        "Registry Available", str(training_result.get("registry_available", 0))
    )
    pdf.metric_row("Primary Metric", training_result.get("primary_metric", "N/A"))

    best = training_result.get("best_model")
    if best:
        pdf.ln(4)
        pdf.sub_title("Champion Model")
        pdf.metric_row("Model", best.get("model_name", "N/A"), highlight=True)
        pdf.metric_row("Family", best.get("family", "N/A"))
        for k, v in best.get("metrics", {}).items():
            if k != "primary":
                label = k.upper() if len(k) <= 4 else k.title()
                pdf.metric_row(label, f"{v:.4f}" if isinstance(v, float) else str(v))
        pdf.metric_row("Training Time", f"{best.get('train_time_sec', 0)}s")

    # ── Leaderboard ──
    leaderboard = training_result.get("leaderboard", [])[:20]
    if leaderboard:
        pdf.ln(4)
        pdf.sub_title("Top 20 Leaderboard")

        primary_metric = training_result.get("primary_metric", "accuracy")
        metric_label = (
            primary_metric.upper()
            if len(primary_metric) <= 4
            else primary_metric.title()
        )

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*NexoraReport.ACCENT)
        col_w = [10, 65, 30, 30, 25, 30]
        headers = ["#", "Model", "Family", metric_label, "Time", "Speed"]
        for h, w in zip(headers, col_w):
            pdf.cell(w, 6, _pdf_text(h), new_x="END")
        pdf.ln()

        pdf.set_draw_color(*NexoraReport.ACCENT)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(1)

        for i, m in enumerate(leaderboard):
            if pdf.get_y() > 260:
                pdf.add_page()
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(
                *(NexoraReport.SECONDARY if i == 0 else NexoraReport.TEXT)
            )
            pdf.cell(col_w[0], 5, str(i + 1), new_x="END")
            pdf.cell(
                col_w[1], 5, _pdf_text(str(m.get("model_name", ""))[:35]), new_x="END"
            )
            pdf.cell(col_w[2], 5, _pdf_text(str(m.get("family", ""))), new_x="END")
            score = m.get("primary_score", 0)
            pdf.cell(
                col_w[3],
                5,
                f"{score:.4f}" if isinstance(score, float) else str(score),
                new_x="END",
            )
            pdf.cell(col_w[4], 5, f"{m.get('train_time_sec', 0)}s", new_x="END")
            pdf.cell(
                col_w[5],
                5,
                _pdf_text(str(m.get("speed", ""))),
                new_x="LMARGIN",
                new_y="NEXT",
            )

    # ── Explainability ──
    if explainability:
        pdf.add_page()
        pdf.section_title("3. Model Explainability (SHAP)")

        pdf.body_text(
            f"SHAP (SHapley Additive exPlanations) analysis was performed on the champion model "
            f"'{explainability.get('model_name', '')}' to understand feature contributions. "
            f"Analysis used {explainability.get('test_count', 0)} test samples across "
            f"{explainability.get('feature_count', 0)} features."
        )

        # Feature importance table
        importances = explainability.get("feature_importance", [])
        if importances:
            pdf.sub_title("Feature Importance Ranking")
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*NexoraReport.ACCENT)
            pdf.cell(10, 6, "#", new_x="END")
            pdf.cell(70, 6, "Feature", new_x="END")
            pdf.cell(40, 6, "Mean |SHAP|", new_x="END")
            pdf.cell(30, 6, "Contribution %", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

            for i, feat in enumerate(importances[:15]):
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(
                    *(NexoraReport.GREEN if i < 3 else NexoraReport.TEXT)
                )
                pdf.cell(10, 5, str(i + 1), new_x="END")
                pdf.cell(70, 5, _pdf_text(str(feat["feature"])[:40]), new_x="END")
                pdf.cell(40, 5, f"{feat['importance']:.6f}", new_x="END")
                pdf.cell(
                    30, 5, f"{feat['percentage']:.1f}%", new_x="LMARGIN", new_y="NEXT"
                )

        # SHAP plots
        plots = explainability.get("plots", {})
        for plot_name, plot_title in [
            ("feature_importance", "Feature Importance Chart"),
            ("shap_summary", "SHAP Summary (Beeswarm)"),
            ("shap_bar", "SHAP Bar Chart"),
            ("prediction_distribution", "Prediction Distribution"),
            ("residuals", "Residual Analysis"),
        ]:
            if plot_name in plots:
                pdf.add_page()
                pdf.sub_title(plot_title)
                pdf.add_base64_image(plots[plot_name], w=175)

    # ── Metrics Summary ──
    if explainability and explainability.get("metrics"):
        pdf.add_page()
        pdf.section_title("4. Final Model Metrics")
        for k, v in explainability["metrics"].items():
            label = k.upper() if len(k) <= 4 else k.title()
            pdf.metric_row(
                label, f"{v:.4f}" if isinstance(v, float) else str(v), highlight=True
            )

    out = pdf.output()
    if isinstance(out, bytearray):
        return bytes(out)
    return out


def generate_pdf_report(
    dataset_info: dict,
    training_result: dict,
    explainability: dict | None = None,
    insights: dict | None = None,
) -> str:
    """Generate a PDF report and return as base64-encoded string."""
    pdf_bytes = _generate_report(
        dataset_info, training_result, explainability, insights
    )
    return base64.b64encode(pdf_bytes).decode("utf-8")


def save_pdf_report(
    dataset_id: str,
    dataset_info: dict,
    training_result: dict,
    explainability: dict | None = None,
    insights: dict | None = None,
) -> Path:
    """Generate and save a PDF report to disk, return the file path."""
    pdf_bytes = _generate_report(
        dataset_info, training_result, explainability, insights
    )
    path = settings.upload_dir / f"{dataset_id}_report.pdf"
    path.write_bytes(pdf_bytes)
    return path
