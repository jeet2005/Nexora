import pandas as pd

from app.services.dataset_analyzer import _infer_datetime, _is_id_like


def detect_problem_type(df: pd.DataFrame, target_column: str) -> dict:
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found.")

    target = df[target_column]
    n = len(df)
    nunique = target.nunique(dropna=True)
    is_dt = _infer_datetime(target)
    is_numeric = pd.api.types.is_numeric_dtype(target) and not is_dt

    hints: list[str] = []

    if is_dt:
        problem_type = "time_series"
        confidence = 0.88
        hints.append(
            "Target appears to be temporal — time-series models recommended.")
    elif is_numeric and nunique > max(20, n * 0.05):
        problem_type = "regression"
        confidence = 0.9
        hints.append(f"Continuous target with {nunique} unique values.")
    elif is_numeric and 2 <= nunique <= 20:
        problem_type = "classification"
        confidence = 0.85
        hints.append(
            f"Numeric target with {nunique} discrete classes — treated as classification."
        )
    elif not is_numeric and nunique >= 2:
        problem_type = "classification"
        confidence = 0.92
        hints.append(f"Categorical target with {nunique} classes.")
    else:
        problem_type = "classification"
        confidence = 0.5
        hints.append(
            "Low cardinality target — verify this is the correct column.")

    datetime_cols = [
        c for c in df.columns if c != target_column and _infer_datetime(df[c])
    ]
    if datetime_cols and problem_type != "time_series":
        hints.append(
            f"Datetime columns detected ({', '.join(datetime_cols[:3])}) — consider time-series mode."
        )

    return {
        "problem_type": problem_type,
        "confidence": round(confidence, 2),
        "target_column": target_column,
        "unique_values": int(nunique),
        "hints": hints,
    }


def suggest_feature_columns(df: pd.DataFrame, target_column: str) -> dict:
    exclude = {target_column}
    id_cols = [c for c in df.columns if c !=
               target_column and _is_id_like(df[c])]
    dt_cols = [c for c in df.columns if c !=
               target_column and _infer_datetime(df[c])]

    features = [
        c
        for c in df.columns
        if c not in exclude and c not in id_cols and c not in dt_cols
    ]

    return {
        "feature_columns": features,
        "excluded_id_columns": id_cols,
        "excluded_datetime_columns": dt_cols,
    }
