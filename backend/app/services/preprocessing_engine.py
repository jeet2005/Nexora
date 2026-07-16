from typing import Any

import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from app.services.dataset_analyzer import _infer_datetime, _is_id_like


class PreprocessingConfig:
    def __init__(
        self,
        missing_strategy: str = "auto",
        outlier_method: str = "iqr_cap",
        scaling: str = "standard",
        encode_categorical: bool = True,
        remove_duplicates: bool = True,
        remove_constant: bool = True,
        drop_id_columns: bool = True,
    ):
        self.missing_strategy = missing_strategy
        self.outlier_method = outlier_method
        self.scaling = scaling
        self.encode_categorical = encode_categorical
        self.remove_duplicates = remove_duplicates
        self.remove_constant = remove_constant
        self.drop_id_columns = drop_id_columns


def _step(name: str, detail: str, affected: int = 0) -> dict:
    return {"step": name, "detail": detail, "affected_rows_or_cols": affected}


def preprocess(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    config: PreprocessingConfig | None = None,
) -> tuple[pd.DataFrame, list[dict], dict[str, Any]]:
    config = config or PreprocessingConfig()
    steps: list[dict] = []
    work = df.copy()
    encoders: dict[str, Any] = {}
    scalers: dict[str, Any] = {}

    # --- Drop ID columns ---
    if config.drop_id_columns:
        id_cols = [
            c for c in work.columns if c != target_column and _is_id_like(work[c])
        ]
        if id_cols:
            work = work.drop(columns=id_cols)
            steps.append(
                _step(
                    "drop_id_columns",
                    f"Removed ID-like columns: {', '.join(id_cols)}",
                    len(id_cols),
                )
            )

    # --- Remove duplicates ---
    if config.remove_duplicates:
        before = len(work)
        work = work.drop_duplicates()
        removed = before - len(work)
        if removed:
            steps.append(
                _step("remove_duplicates", f"Removed {removed} duplicate rows", removed)
            )

    # --- Remove constant columns ---
    if config.remove_constant:
        constant = [
            c
            for c in work.columns
            if c != target_column and work[c].nunique(dropna=True) <= 1
        ]
        if constant:
            work = work.drop(columns=constant)
            steps.append(
                _step(
                    "remove_constant",
                    f"Dropped constant columns: {', '.join(constant)}",
                    len(constant),
                )
            )

    # --- Datetime columns → drop for now (Phase 3 will use them) ---
    dt_cols = [
        c for c in work.columns if c != target_column and _infer_datetime(work[c])
    ]
    if dt_cols:
        work = work.drop(columns=dt_cols)
        steps.append(
            _step(
                "drop_datetime",
                f"Set aside datetime columns for time-series phase: {', '.join(dt_cols)}",
                len(dt_cols),
            )
        )

    feature_cols = [c for c in work.columns if c != target_column]

    # --- Missing values ---
    for col in work.columns:
        missing = work[col].isna().sum()
        if missing == 0:
            continue

        if col == target_column:
            before = len(work)
            work = work.dropna(subset=[target_column])
            steps.append(
                _step(
                    "drop_missing_target",
                    f"Dropped {before - len(work)} rows with missing target",
                    before - len(work),
                )
            )
            continue

        if (
            work[col].dtype in ("object", "category")
            or work[col].nunique(dropna=True) < 20
        ):
            mode_val = work[col].mode()
            fill = mode_val.iloc[0] if len(mode_val) else "unknown"
            work[col] = work[col].fillna(fill)
            steps.append(
                _step(
                    "fill_missing",
                    f"Filled {missing} missing in '{col}' with mode",
                    missing,
                )
            )
        else:
            work[col] = work[col].fillna(work[col].median())
            steps.append(
                _step(
                    "fill_missing",
                    f"Filled {missing} missing in '{col}' with median",
                    missing,
                )
            )

    # --- Outlier capping (numeric features only) ---
    if config.outlier_method == "iqr_cap":
        for col in feature_cols:
            if not pd.api.types.is_numeric_dtype(work[col]):
                continue
            s = work[col]
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            capped = ((s < low) | (s > high)).sum()
            if capped:
                work[col] = s.clip(low, high)
                steps.append(
                    _step(
                        "outlier_cap",
                        f"Capped {capped} outliers in '{col}' (IQR)",
                        int(capped),
                    )
                )

    # --- Encode categoricals ---
    if config.encode_categorical:
        for col in feature_cols:
            if col not in work.columns:
                continue
            if pd.api.types.is_numeric_dtype(work[col]):
                continue
            nunique = work[col].nunique()
            if nunique <= 2:
                le = LabelEncoder()
                work[col] = le.fit_transform(work[col].astype(str))
                encoders[col] = "label"
                steps.append(
                    _step(
                        "label_encode", f"Label-encoded binary column '{col}'", nunique
                    )
                )
            else:
                dummies = pd.get_dummies(
                    work[col].astype(str), prefix=col, drop_first=True
                )
                dummies.columns = [str(c).replace(" ", "_") for c in dummies.columns]
                work = work.drop(columns=[col])
                work = pd.concat([work, dummies], axis=1)
                encoders[col] = "onehot"
                steps.append(
                    _step(
                        "onehot_encode",
                        f"One-hot encoded '{col}' → {len(dummies.columns)} columns",
                        len(dummies.columns),
                    )
                )

    # Recompute feature cols after encoding
    feature_cols = [c for c in work.columns if c != target_column]
    numeric_features = [
        c for c in feature_cols if pd.api.types.is_numeric_dtype(work[c])
    ]

    # --- Scale numeric features ---
    if config.scaling == "standard" and numeric_features:
        scaler = StandardScaler()
        work[numeric_features] = scaler.fit_transform(work[numeric_features])
        scalers["features"] = "standard"
        steps.append(
            _step(
                "scale",
                f"StandardScaler applied to {len(numeric_features)} features",
                len(numeric_features),
            )
        )
    elif config.scaling == "minmax" and numeric_features:
        scaler = MinMaxScaler()
        work[numeric_features] = scaler.fit_transform(work[numeric_features])
        scalers["features"] = "minmax"
        steps.append(
            _step(
                "scale",
                f"MinMaxScaler applied to {len(numeric_features)} features",
                len(numeric_features),
            )
        )

    if not steps:
        steps.append(
            _step("no_changes", "Dataset required no preprocessing transformations", 0)
        )

    meta = {
        "rows_before": len(df),
        "rows_after": len(work),
        "columns_before": len(df.columns),
        "columns_after": len(work.columns),
        "feature_count": len(feature_cols),
        "encoders": encoders,
        "scalers": scalers,
    }

    return work, steps, meta
