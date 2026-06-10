"""Dataset loading utilities for the Nexora MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nexora.types import LoadedData


def load_source(
    source: str | Path | pd.DataFrame | np.ndarray,
    y: Any | None = None,
    *,
    feature_names: list[str] | None = None,
) -> LoadedData:
    """Load a supported tabular input into a DataFrame.

    Args:
        source: CSV path, pandas DataFrame, or NumPy feature matrix.
        y: Optional NumPy target vector when `source` is an array.
        feature_names: Optional feature names for NumPy arrays.

    Returns:
        LoadedData containing a DataFrame and source metadata.

    Example:
        `loaded = load_source("sales.csv")`
    """

    if isinstance(source, pd.DataFrame):
        return LoadedData(
            dataframe=source.copy(),
            source_path=None,
            source_name="dataframe",
        )

    if isinstance(source, np.ndarray):
        names = feature_names or [f"feature_{i}" for i in range(source.shape[1])]
        if len(names) != source.shape[1]:
            raise ValueError("feature_names must match the NumPy feature width.")
        df = pd.DataFrame(source, columns=names)
        if y is not None:
            df["target"] = y
        return LoadedData(dataframe=df, source_path=None, source_name="numpy_array")

    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {path}")
    if path.suffix.lower() != ".csv":
        raise ValueError(
            f"Nexora v0.1.0 supports CSV files for package entry. Got: {path.suffix}"
        )

    try:
        import duckdb
        df = duckdb.query(f"SELECT * FROM '{path.as_posix()}'").df()
    except ImportError:
        # Fallback if duckdb is somehow not installed
        df = pd.read_csv(path, low_memory=False)

    if df.empty:
        raise ValueError(f"Dataset is empty: {path}")
    return LoadedData(dataframe=df, source_path=path, source_name=path.name)

