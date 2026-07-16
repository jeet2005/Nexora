from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.models.schemas import ClusteringResult, TimeSeriesResult
from app.services.dataset_analyzer import _infer_datetime, _is_id_like
from app.services.dataset_store import load_dataframe
from app.services.experiment_service import create_experiment


def _result_path(dataset_id: str, suffix: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.{suffix}.json"


def _json_ready(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else round(float(value), 6)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def _feature_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    work = pd.DataFrame(index=df.index)
    for column in columns:
        series = df[column]
        if _infer_datetime(series):
            parsed = pd.to_datetime(series, errors="coerce", format="mixed")
            work[f"{column}__year"] = parsed.dt.year
            work[f"{column}__month"] = parsed.dt.month
            work[f"{column}__day"] = parsed.dt.day
        else:
            work[column] = series
    work = pd.get_dummies(work, dummy_na=True)
    work = work.apply(pd.to_numeric, errors="coerce")
    return work.fillna(work.median(numeric_only=True)).fillna(0)


def run_clustering(
    dataset_id: str, n_clusters: int, feature_columns: list[str] | None = None
) -> ClusteringResult:
    df = load_dataframe(dataset_id)
    if df is None:
        raise ValueError("Dataset not found.")

    columns = feature_columns or [
        column
        for column in df.columns
        if not _is_id_like(df[column]) and df[column].nunique(dropna=True) > 1
    ]
    columns = [column for column in columns if column in df.columns]
    if len(columns) < 1:
        raise ValueError(
            "At least one usable feature column is required for clustering."
        )
    if len(df) < n_clusters:
        raise ValueError("Number of clusters cannot exceed the row count.")

    X_raw = _feature_frame(df, columns)
    X = StandardScaler().fit_transform(X_raw)
    model = KMeans(n_clusters=n_clusters, n_init=10, random_state=settings.random_seed)
    labels = model.fit_predict(X)
    pca = PCA(n_components=2, random_state=settings.random_seed)
    coords = (
        pca.fit_transform(X) if X.shape[1] >= 2 else np.c_[X[:, 0], np.zeros(len(X))]
    )

    silhouette = (
        float(silhouette_score(X, labels))
        if n_clusters > 1 and len(set(labels)) > 1
        else 0.0
    )
    clusters: list[dict[str, Any]] = []
    labeled = df.copy()
    labeled["cluster"] = labels
    for cluster_id in range(n_clusters):
        part = labeled[labeled["cluster"] == cluster_id]
        profile: dict[str, Any] = {}
        for column in columns[:8]:
            series = part[column]
            if pd.api.types.is_numeric_dtype(series):
                profile[column] = round(
                    pd.to_numeric(series, errors="coerce").mean(), 4
                )
            else:
                mode = series.dropna().astype(str).mode()
                profile[column] = mode.iloc[0] if len(mode) else None
        clusters.append(
            {
                "cluster": cluster_id,
                "size": len(part),
                "percentage": round(100 * len(part) / max(len(df), 1), 2),
                "profile": profile,
            }
        )

    preview = df.head(100).copy()
    preview["cluster"] = labels[: len(preview)]
    preview["cluster_x"] = coords[: len(preview), 0]
    preview["cluster_y"] = coords[: len(preview), 1]
    preview_rows = preview.replace({np.nan: None}).to_dict(orient="records")

    result = ClusteringResult(
        dataset_id=dataset_id,
        run_id=str(uuid.uuid4()),
        n_clusters=n_clusters,
        feature_columns=columns,
        metrics={
            "silhouette": round(silhouette, 4),
            "inertia": round(model.inertia_, 4),
        },
        clusters=clusters,
        preview=[
            {str(key): _json_ready(value) for key, value in row.items()}
            for row in preview_rows
        ],
        created_at=datetime.now(UTC).isoformat(),
    )
    _result_path(dataset_id, "clustering").write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )
    create_experiment(
        dataset_id,
        "clustering",
        "clustering",
        config={
            "n_clusters": n_clusters,
            "feature_columns": columns,
            "seed": settings.random_seed,
        },
        metrics=result.metrics,
        artifact_refs={"result": str(_result_path(dataset_id, "clustering"))},
    )
    return result


def load_clustering(dataset_id: str) -> ClusteringResult | None:
    path = _result_path(dataset_id, "clustering")
    if not path.exists():
        return None
    return ClusteringResult.model_validate_json(path.read_text(encoding="utf-8"))


def _freq_offset(freq: str):
    if freq == "D":
        return pd.DateOffset(days=1)
    if freq == "W":
        return pd.DateOffset(weeks=1)
    return pd.DateOffset(months=1)


def _grouper_freq(frequency: str) -> str:
    """Map user-facing frequency codes to pandas Grouper aliases."""
    mapping = {"D": "D", "W": "W", "M": "ME"}
    return mapping.get(frequency, frequency)


def run_time_series(
    dataset_id: str,
    date_column: str,
    target_column: str,
    periods: int,
    frequency: str,
) -> TimeSeriesResult:
    df = load_dataframe(dataset_id)
    if df is None:
        raise ValueError("Dataset not found.")
    if date_column not in df.columns or target_column not in df.columns:
        raise ValueError("Date and target columns must exist in the dataset.")

    series = df[[date_column, target_column]].copy()
    if pd.api.types.is_numeric_dtype(series[date_column]):
        # Try seconds first, if they are huge it will be out of bounds for 's' usually, or we can check magnitude
        # But pandas unit='s' works for both if we are careful, actually unit='ms' or 's'
        if series[date_column].mean() > 946684800000:
            series[date_column] = pd.to_datetime(
                series[date_column], unit="ms", errors="coerce"
            )
        else:
            series[date_column] = pd.to_datetime(
                series[date_column], unit="s", errors="coerce"
            )
    else:
        series[date_column] = pd.to_datetime(
            series[date_column], errors="coerce", format="mixed"
        )
    series[target_column] = pd.to_numeric(series[target_column], errors="coerce")
    series = series.dropna().sort_values(date_column)
    if len(series) < 6:
        raise ValueError(
            "At least six dated numeric observations are required for forecasting."
        )

    # Bypass pd.Grouper/resample due to Python 3.12 C-extension segfaults
    # We group using Python's native datetime.date to avoid Cython period/resample bugs
    from datetime import date, timedelta

    raw_dates = series[date_column].tolist()
    py_dates = []
    for d in raw_dates:
        if hasattr(d, "to_pydatetime"):
            py_dates.append(d.to_pydatetime().date())
        elif hasattr(d, "date"):
            py_dates.append(d.date())
        else:
            py_dates.append(d)

    if frequency == "D":
        group_keys = py_dates
    elif frequency == "W":
        group_keys = [d - timedelta(days=d.weekday()) for d in py_dates]
    else:  # M
        group_keys = [date(d.year, d.month, 1) for d in py_dates]

    series["_group_key"] = group_keys
    grouped = series.groupby("_group_key")[target_column].mean().dropna()
    grouped.index = pd.to_datetime(grouped.index)
    if len(grouped) < 6:
        raise ValueError(
            "Not enough observations remain after grouping by the selected frequency."
        )

    t = cast(Any, np.arange(len(grouped)).reshape(-1, 1))
    y = cast(Any, grouped.values.astype(float))
    holdout = max(2, min(6, len(grouped) // 4))
    model = LinearRegression()
    model.fit(t[:-holdout], y[:-holdout])
    pred_test = model.predict(t[-holdout:])
    metrics = {
        "mae": round(mean_absolute_error(y[-holdout:], pred_test), 4),
        "r2": round(r2_score(y[-holdout:], pred_test), 4) if holdout >= 2 else 0.0,
    }

    model.fit(t, y)
    future_t = cast(Any, np.arange(len(grouped), len(grouped) + periods).reshape(-1, 1))
    future_values = model.predict(future_t)
    offset = _freq_offset(frequency)
    current = grouped.index[-1]
    forecast = []
    for value in future_values:
        current = current + offset
        forecast.append(
            {"date": current.date().isoformat(), "prediction": round(value, 4)}
        )

    history = [
        {"date": cast(Any, index).date().isoformat(), "value": round(value, 4)}
        for index, value in grouped.tail(120).items()
    ]
    result = TimeSeriesResult(
        dataset_id=dataset_id,
        run_id=str(uuid.uuid4()),
        date_column=date_column,
        target_column=target_column,
        frequency=frequency,
        periods=periods,
        metrics=metrics,
        history=history,
        forecast=forecast,
        created_at=datetime.now(UTC).isoformat(),
    )
    _result_path(dataset_id, "time_series").write_text(
        result.model_dump_json(indent=2), encoding="utf-8"
    )
    create_experiment(
        dataset_id,
        "time_series",
        "time_series",
        target_column=target_column,
        config={"date_column": date_column, "periods": periods, "frequency": frequency},
        metrics=metrics,
        artifact_refs={"result": str(_result_path(dataset_id, "time_series"))},
    )
    return result


def load_time_series(dataset_id: str) -> TimeSeriesResult | None:
    path = _result_path(dataset_id, "time_series")
    if not path.exists():
        return None
    return TimeSeriesResult.model_validate_json(path.read_text(encoding="utf-8"))
