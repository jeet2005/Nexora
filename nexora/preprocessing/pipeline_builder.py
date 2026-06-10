"""Build fitted-safe sklearn preprocessing pipelines."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from nexora.profiler.dataset_profile import infer_datetime, is_id_like
from nexora.types import PreprocessingBundle, PreprocessingSchema


def build_preprocessing(df: pd.DataFrame, target: str) -> PreprocessingBundle:
    """Create dataset-specific preprocessing decisions and an unfitted transformer.

    Args:
        df: Training dataframe.
        target: Target column name.

    Returns:
        PreprocessingBundle containing an sklearn ColumnTransformer.

    Example:
        `bundle = build_preprocessing(df, "revenue")`
    """

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found.")

    work = df.copy()
    before = len(work)
    work = work.dropna(subset=[target])
    if work.empty:
        raise ValueError(f"All rows have missing target values for '{target}'.")
    if before != len(work):
        work = work.reset_index(drop=True)

    candidate_features = [col for col in work.columns if col != target]
    id_columns = [col for col in candidate_features if is_id_like(work[col])]
    datetime_columns = [
        col
        for col in candidate_features
        if col not in id_columns and infer_datetime(work[col])
    ]
    # Constant columns are retained to ensure models have features even when data is low variance.
    constant_columns = []
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

    transformer = _make_column_transformer(numeric_features, categorical_features, text_features)
    
    # Build decision log
    decision_log = {}
    for col in id_columns:
        decision_log[col] = "Dropped (high cardinality ID-like)"
    for col in datetime_columns:
        decision_log[col] = "Dropped (datetime column)"
    for col in constant_columns:
        decision_log[col] = "Dropped (constant value)"
    for col in numeric_features:
        decision_log[col] = "Imputed (median) & Scaled (StandardScaler)"
    for col in categorical_features:
        decision_log[col] = "Imputed (mode) & Encoded (OneHot)"
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
    numeric_features: list[str], categorical_features: list[str], text_features: list[str] = None
) -> ColumnTransformer:
    if text_features is None:
        text_features = []
        
    transformers = []
    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", _one_hot_encoder()),
                    ]
                ),
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


def _one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)
