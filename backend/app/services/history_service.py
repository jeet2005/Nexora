from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.models.schemas import DatasetHistoryItem
from app.services.dataset_store import load_analysis
from app.services.deployed_model_service import load_production_status
from app.services.persistence_service import upsert
from app.services.session_store import load_session
from app.services.training_manager import load_training_result


def _archive_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.archive.json"


def _metadata_paths() -> list[Path]:
    return sorted(
        settings.upload_dir.glob("*.meta.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _read_archived(dataset_id: str) -> bool:
    path = _archive_path(dataset_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("archived"))
    except (OSError, ValueError):
        return False


def set_archived(dataset_id: str, archived: bool) -> None:
    if not load_analysis(dataset_id):
        raise ValueError("Dataset not found.")
    _archive_path(dataset_id).write_text(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "archived": archived,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    record = history_item(dataset_id)
    if record:
        upsert("datasets", {"dataset_id": dataset_id}, record.model_dump())


def _user_path(dataset_id: str) -> Path:
    return settings.upload_dir / f"{dataset_id}.user.json"


def _read_user_id(dataset_id: str) -> str | None:
    path = _user_path(dataset_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("user_id")
    except (OSError, ValueError):
        return None


def history_item(
    dataset_id: str, user_id: str | None = None
) -> DatasetHistoryItem | None:
    analysis = load_analysis(dataset_id)
    if not analysis:
        return None

    if user_id:
        try:
            _user_path(dataset_id).write_text(
                json.dumps({"dataset_id": dataset_id, "user_id": user_id}),
                encoding="utf-8",
            )
        except OSError:
            pass
    else:
        user_id = _read_user_id(dataset_id)

    try:
        session = load_session(dataset_id)
    except Exception:
        session = None

    try:
        training = load_training_result(dataset_id)
    except Exception:
        training = None

    try:
        production = load_production_status(dataset_id)
    except Exception:
        production = None
    meta_path = settings.upload_dir / f"{dataset_id}.meta.json"
    report_path = settings.upload_dir / f"{dataset_id}_report.pdf"
    stat = meta_path.stat() if meta_path.exists() else None

    last_model = None
    trained_count = 0
    if production and production.models:
        trained_count = len(production.models)
        last_model = production.models[0].model_name
    elif training and training.best_model:
        trained_count = training.total_completed
        last_model = training.best_model.model_name

    item = DatasetHistoryItem(
        dataset_id=dataset_id,
        filename=analysis.filename,
        rows=analysis.rows,
        columns=analysis.columns,
        health_score=analysis.health.overall,
        status=session.status if session else "analyzed",
        target_column=session.target_column if session else None,
        problem_type=session.problem_type if session else None,
        last_trained_model=last_model,
        trained_model_count=trained_count,
        report_available=report_path.exists(),
        archived=_read_archived(dataset_id),
        created_at=datetime.fromtimestamp(stat.st_ctime, UTC).isoformat()
        if stat
        else None,
        updated_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
        if stat
        else None,
    )
    record = item.model_dump()
    if user_id:
        record["user_id"] = user_id
    upsert("datasets", {"dataset_id": dataset_id}, record)
    return item


def list_history(
    include_archived: bool = False, user_id: str | None = None
) -> list[DatasetHistoryItem]:
    # Try MongoDB first
    from app.services.persistence_service import find

    query = {"user_id": user_id} if user_id else {}
    db_items = find("datasets", query)
    if db_items:
        out = []
        for doc in db_items:
            try:
                item = DatasetHistoryItem.model_validate(doc)
                if item.archived and not include_archived:
                    continue
                out.append(item)
            except Exception:
                continue
        if out:
            out.sort(key=lambda x: x.updated_at or x.created_at or "", reverse=True)
            return out

    # Local disk fallback
    items: list[DatasetHistoryItem] = []
    for path in _metadata_paths():
        dataset_id = path.name.replace(".meta.json", "")
        item_user_id = _read_user_id(dataset_id)
        if user_id and item_user_id != user_id:
            continue
        item = history_item(dataset_id)
        if not item:
            continue
        if item.archived and not include_archived:
            continue
        items.append(item)
    return items


def delete_dataset(dataset_id: str) -> None:
    if not load_analysis(dataset_id):
        raise ValueError("Dataset not found.")

    root = settings.upload_dir.resolve()
    targets = list(settings.upload_dir.glob(f"{dataset_id}*"))
    for target in targets:
        resolved = target.resolve()
        if root not in resolved.parents and resolved != root:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
