"""Anomaly scoring engine — Isolation Forest + lightweight Autoencoder ensemble.

The Autoencoder is implemented as a single-hidden-layer neural network using
only NumPy (no PyTorch/TensorFlow dependency).  Combined with scikit-learn's
IsolationForest, this gives sub-10 ms per-row scoring.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ── Feature columns used for scoring ────────────────────────────────────────
NUMERIC_FEATURES = [
    "src_port",
    "dst_port",
    "bytes_sent",
    "bytes_received",
    "duration_ms",
    "packet_count",
    "is_encrypted",
]
CATEGORICAL_FEATURES = ["protocol", "tcp_flags"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# ── Threat-level thresholds ─────────────────────────────────────────────────
THRESHOLDS = {"LOW": 0.3, "MEDIUM": 0.6, "HIGH": 0.8}


def _threat_level(score: float) -> str:
    if score < THRESHOLDS["LOW"]:
        return "LOW"
    elif score < THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    elif score < THRESHOLDS["HIGH"]:
        return "HIGH"
    return "CRITICAL"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Lightweight NumPy Autoencoder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _NumpyAutoencoder:
    """Single-hidden-layer autoencoder for reconstruction-error anomaly detection."""

    def __init__(
        self, input_dim: int, hidden_dim: int = 4, lr: float = 0.005, epochs: int = 100
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.epochs = epochs

        # Xavier initialisation
        limit1 = np.sqrt(6.0 / (input_dim + hidden_dim))
        self.W1 = np.random.uniform(-limit1, limit1, (input_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)

        limit2 = np.sqrt(6.0 / (hidden_dim + input_dim))
        self.W2 = np.random.uniform(-limit2, limit2, (hidden_dim, input_dim))
        self.b2 = np.zeros(input_dim)

    @staticmethod
    def _relu(x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    @staticmethod
    def _relu_deriv(x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)

    def _forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        z1 = X @ self.W1 + self.b1
        a1 = self._relu(z1)
        z2 = a1 @ self.W2 + self.b2
        return z1, a1, z2

    def fit(self, X: np.ndarray) -> None:
        n = X.shape[0]
        for _ in range(self.epochs):
            z1, a1, reconstruction = self._forward(X)
            # MSE loss gradient
            error = reconstruction - X  # (n, input_dim)
            dW2 = (a1.T @ error) / n
            db2 = error.mean(axis=0)
            da1 = error @ self.W2.T
            dz1 = da1 * self._relu_deriv(z1)
            dW1 = (X.T @ dz1) / n
            db1 = dz1.mean(axis=0)

            self.W1 -= self.lr * dW1
            self.b1 -= self.lr * db1
            self.W2 -= self.lr * dW2
            self.b2 -= self.lr * db2

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Per-row MSE reconstruction error."""
        _, _, recon = self._forward(X)
        return np.mean((X - recon) ** 2, axis=1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Scorer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AnomalyScorer:
    """Ensemble anomaly scorer: Isolation Forest (0.5) + Autoencoder (0.5)."""

    def __init__(self, csv_path: str | Path | None = None) -> None:
        self.ready = False
        self._scaler = StandardScaler()
        self._label_encoders: dict[str, LabelEncoder] = {}
        self._iso_forest: IsolationForest | None = None
        self._autoencoder: _NumpyAutoencoder | None = None
        self._feature_names: list[str] = []
        self._feature_stds: np.ndarray | None = None

        if csv_path is not None:
            self.train(csv_path)

    def train(self, csv_path: str | Path) -> None:
        """Train both models on the CSV data."""
        df = pd.read_csv(csv_path)
        X = self._prepare_features(df, fit=True)

        # Isolation Forest
        self._iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1,
        )
        self._iso_forest.fit(cast(Any, X))

        # Autoencoder
        self._autoencoder = _NumpyAutoencoder(
            input_dim=X.shape[1], hidden_dim=max(3, X.shape[1] // 2), epochs=150
        )
        self._autoencoder.fit(X)

        # Pre-compute feature standard deviations for feature-importance ranking
        self._feature_stds = np.std(X, axis=0) + 1e-8
        self._feature_names = NUMERIC_FEATURES + [
            f"{col}_enc" for col in CATEGORICAL_FEATURES
        ]
        self.ready = True

    def _prepare_features(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        """Convert raw dataframe to a numeric feature matrix."""
        parts: list[np.ndarray] = []

        # Numeric columns
        num_cols = [c for c in NUMERIC_FEATURES if c in df.columns]
        if fit:
            num_data = np.asarray(
                self._scaler.fit_transform(df[num_cols].values.astype(float))
            )
        else:
            num_data = np.asarray(
                self._scaler.transform(df[num_cols].values.astype(float))
            )
        parts.append(num_data)

        # Categorical columns — label-encode
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                if fit:
                    le = LabelEncoder()
                    encoded = np.asarray(
                        le.fit_transform(df[col].astype(str).to_list())
                    )
                    self._label_encoders[col] = le
                else:
                    le = self._label_encoders[col]
                    vals = df[col].astype(str).values
                    # Handle unseen labels gracefully
                    mapped = []
                    for v in vals:
                        if v in le.classes_:
                            mapped.append(
                                int(np.asarray(le.transform([v]))[0]))
                        else:
                            mapped.append(len(le.classes_))
                    encoded = np.array(mapped)
                parts.append(encoded.reshape(-1, 1).astype(float))

        return np.hstack(parts)

    def _prepare_single(self, row: dict[str, Any]) -> np.ndarray:
        """Convert a single row dict to a feature vector."""
        df = pd.DataFrame([row])
        return self._prepare_features(df, fit=False)

    def score(self, row: dict[str, Any]) -> dict[str, Any]:
        """Score a single row. Returns anomaly_score, threat_level, top_features.

        Target: <10ms per row.
        """
        if not self.ready or self._iso_forest is None or self._autoencoder is None:
            raise RuntimeError("Scorer not trained yet")

        t0 = time.perf_counter_ns()
        X = self._prepare_single(row)

        # Isolation Forest: score_samples returns negative anomaly score
        # More negative = more anomalous. Normalize to [0, 1].
        # type: ignore[union-attr]
        if_raw = -self._iso_forest.score_samples(X)[0]
        # Typical range is roughly [-0.5, 0.5] after negation; map to [0, 1]
        if_score = float(np.clip((if_raw + 0.5) / 1.0, 0.0, 1.0))

        # Autoencoder: reconstruction error, normalized
        ae_error = float(self._autoencoder.reconstruction_error(X)[
                         0])  # type: ignore[union-attr]
        # Normalize using a sigmoid-like mapping
        ae_score = float(1.0 / (1.0 + np.exp(-2.0 * (ae_error - 1.0))))

        # Ensemble (equal weight)
        combined = 0.5 * if_score + 0.5 * ae_score
        combined = float(np.clip(combined, 0.0, 1.0))

        # Top features: largest absolute deviation from mean (z-score magnitude)
        feature_deviations = np.abs(
            X[0]) / (self._feature_stds + 1e-8)  # type: ignore[operator]
        top_indices = np.argsort(feature_deviations)[-3:][::-1]
        top_feats = [
            self._feature_names[i] for i in top_indices if i < len(self._feature_names)
        ]

        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000

        return {
            "anomaly_score": round(combined, 4),
            "threat_level": _threat_level(combined),
            "top_features": top_feats,
            "_scoring_ms": round(elapsed_ms, 2),
        }
