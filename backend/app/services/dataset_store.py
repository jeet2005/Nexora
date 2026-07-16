from pathlib import Path

import pandas as pd

from app.config import settings
from app.models.schemas import DatasetAnalysis
from app.services.dataset_analyzer import analyze_dataset


def _meta_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.meta.json"


def _csv_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.csv"


def save_dataset(df: pd.DataFrame, filename: str, analysis: DatasetAnalysis) -> None:
    df.to_csv(_csv_path(analysis.dataset_id), index=False)
    _meta_path(analysis.dataset_id).write_text(
        analysis.model_dump_json(indent=2), encoding="utf-8"
    )
    from app.services.persistence_service import upsert

    upsert(
        "dataset_analyses", {
            "dataset_id": analysis.dataset_id}, analysis.model_dump()
    )


def load_analysis(dataset_id: str) -> DatasetAnalysis | None:
    path = _meta_path(dataset_id)
    if not path.exists():
        from app.services.persistence_service import find

        db_items = find("dataset_analyses", {"dataset_id": dataset_id})
        if db_items:
            try:
                return DatasetAnalysis.model_validate(db_items[0])
            except Exception:
                pass
        return None
    analysis = DatasetAnalysis.model_validate_json(
        path.read_text(encoding="utf-8"))
    if not analysis.model_eligibility:
        df = load_dataframe(dataset_id)
        if df is not None:
            analysis = analyze_dataset(df, analysis.filename, dataset_id)
            try:
                path.write_text(analysis.model_dump_json(
                    indent=2), encoding="utf-8")
                from app.services.persistence_service import upsert

                upsert(
                    "dataset_analyses",
                    {"dataset_id": dataset_id},
                    analysis.model_dump(),
                )
            except OSError:
                # Returning refreshed analysis is enough when legacy metadata storage is read-only.
                pass
    return analysis


def load_dataframe(dataset_id: str) -> pd.DataFrame | None:
    path = _csv_path(dataset_id)
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)
