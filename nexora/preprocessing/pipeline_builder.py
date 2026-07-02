"""Build fitted-safe sklearn preprocessing pipelines."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler

from nexora.profiler.dataset_profile import infer_datetime, is_id_like
from nexora.types import PreprocessingBundle, PreprocessingConfig, PreprocessingSchema


def build_preprocessing(
    df: pd.DataFrame,
    target: str,
    config: PreprocessingConfig | None = None,
) -> PreprocessingBundle:
    """Create dataset-specific preprocessing decisions and an unfitted transformer.

    Args:
        df: Training dataframe.
        target: Target column name.

    Returns:
        PreprocessingBundle containing an sklearn ColumnTransformer.

    Example:
        `bundle = build_preprocessing(df, "revenue")`
    """

    config = config or PreprocessingConfig()
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found.")

    work = df.copy()
    if config.remove_duplicates:
        work = work.drop_duplicates().reset_index(drop=True)
    before = len(work)
    work = work.dropna(subset=[target])
    if work.empty:
        raise ValueError(f"All rows have missing target values for '{target}'.")
    if before != len(work):
        work = work.reset_index(drop=True)

    candidate_features = [col for col in work.columns if col != target]
    id_columns = [
        col
        for col in candidate_features
        if config.drop_id_columns and is_id_like(work[col])
    ]
    datetime_columns = [
        col
        for col in candidate_features
        if col not in id_columns and infer_datetime(work[col])
    ]
    constant_columns = [
        col
        for col in candidate_features
        if config.remove_constant
        and col not in id_columns
        and work[col].nunique(dropna=True) <= 1
    ]
    dropped = id_columns + datetime_columns + constant_columns
    features = [col for col in candidate_features if col not in set(dropped)]
    if not features:
        raise ValueError("No usable feature columns remain after preprocessing checks.")

    numeric_features = [
        col for col in features if pd.api.types.is_numeric_dtype(work[col])
    ]

    # Heuristic for text vs categorical
    text_features = []
    categorical_features = []

    for col in features:
        if col in numeric_features:
            continue

        # If it's a string/object type, check unique values and length
        nunique = work[col].nunique(dropna=True)
        if nunique > 20:
            # Let's check average string length
            avg_len = work[col].dropna().astype(str).str.len().mean()
            if avg_len > 30:
                text_features.append(col)
                continue

        categorical_features.append(col)

    if config.outlier_cap:
        work = _cap_outliers(work, numeric_features)

    transformer = _make_column_transformer(
        numeric_features,
        categorical_features,
        text_features,
        config=config,
    )

    # Build decision log
    decision_log = {}
    for col in id_columns:
        decision_log[col] = "Dropped (high cardinality ID-like)"
    for col in datetime_columns:
        decision_log[col] = "Dropped (datetime column)"
    for col in constant_columns:
        decision_log[col] = "Dropped (constant value)"
    for col in numeric_features:
        missing = (
            "Imputed (median)"
            if config.fill_missing
            else "Missing values passed through"
        )
        scaling = {
            "standard": "StandardScaler",
            "minmax": "MinMaxScaler",
            "none": "No scaling",
        }[config.scaling]
        outliers = " & IQR capped" if config.outlier_cap else ""
        decision_log[col] = f"{missing} & {scaling}{outliers}"
    for col in categorical_features:
        if config.encode_categorical:
            decision_log[col] = "Imputed (mode) & Encoded (OneHot)"
        else:
            decision_log[col] = "Dropped (categorical encoding disabled)"
    for col in text_features:
        decision_log[col] = "Embedded (sentence-transformers)"

    # We add text_features to schema manually if needed, or just keep it simple
    schema = PreprocessingSchema(
        target=target,
        feature_columns=features,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        dropped_columns=dropped,
        id_columns=id_columns,
        datetime_columns=datetime_columns,
        constant_columns=constant_columns,
        decision_log=decision_log,
    )
    # Patch schema with text_features if we define it, but for MVP we might not need to if we just pass it to transformer
    schema.text_features = text_features

    return PreprocessingBundle(
        transformer=transformer,
        schema=schema,
        training_frame=work,
    )


def transform_features(df: pd.DataFrame, bundle: PreprocessingBundle):
    """Transform a dataframe with a fitted preprocessing bundle.

    Args:
        df: New dataframe containing the training feature columns.
        bundle: Fitted preprocessing bundle.

    Returns:
        Numeric feature matrix.

    Example:
        `X = transform_features(new_df, bundle)`
    """

    missing = [col for col in bundle.schema.feature_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing)}")
    return bundle.transformer.transform(df[bundle.schema.feature_columns])


def _make_column_transformer(
    numeric_features: list[str],
    categorical_features: list[str],
    text_features: list[str] = None,
    *,
    config: PreprocessingConfig | None = None,
) -> ColumnTransformer:
    config = config or PreprocessingConfig()
    if text_features is None:
        text_features = []

    transformers = []
    if numeric_features:
        numeric_steps = []
        if config.fill_missing:
            numeric_steps.append(("imputer", SimpleImputer(strategy="median")))
        if config.scaling == "standard":
            numeric_steps.append(("scaler", StandardScaler()))
        elif config.scaling == "minmax":
            numeric_steps.append(("scaler", MinMaxScaler()))
        if not numeric_steps:
            numeric_steps.append(("imputer", SimpleImputer(strategy="median")))
        transformers.append(
            (
                "numeric",
                Pipeline(steps=numeric_steps),
                numeric_features,
            )
        )
    if categorical_features and config.encode_categorical:
        cat_steps = []
        if config.fill_missing:
            cat_steps.append(("imputer", SimpleImputer(strategy="most_frequent")))
        cat_steps.append(("onehot", _one_hot_encoder()))
        transformers.append(
            (
                "categorical",
                Pipeline(steps=cat_steps),
                categorical_features,
            )
        )
    if text_features:
        from nexora.preprocessing.text_processor import SentenceTransformerEncoder

        transformers.append(
            (
                "text",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="")),
                        ("embedder", SentenceTransformerEncoder()),
                    ]
                ),
                text_features,
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _cap_outliers(work: pd.DataFrame, numeric_features: list[str]) -> pd.DataFrame:
    out = work.copy()
    for col in numeric_features:
        if pd.api.types.is_bool_dtype(out[col]):
            continue
        series = pd.to_numeric(out[col], errors="coerce")
        clean = series.dropna()
        if len(clean) < 4:
            continue
        q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out[col] = series.clip(low, high)
    return out


def _one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)
