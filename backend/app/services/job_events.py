"""Hybrid MongoDB & In-Memory job status for background training jobs.

Uses an in-memory dictionary for instant local fallback, while mirroring
to MongoDB when available. Ensures training events, progress, and arena
leaderboard work flawlessly offline or when MongoDB is unavailable.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.services.persistence_service import collection

_memory_jobs: dict[str, dict[str, Any]] = {}


def set_job(dataset_id: str, job: dict[str, Any]) -> None:
    if "events" not in job:
        job["events"] = []
    _memory_jobs[dataset_id] = job.copy()
    coll = collection("jobs")
    if coll is not None:
        try:
            coll.update_one({"dataset_id": dataset_id}, {"$set": job}, upsert=True)
        except Exception:
            pass


def update_job(dataset_id: str, **fields: Any) -> dict[str, Any] | None:
    if dataset_id in _memory_jobs:
        _memory_jobs[dataset_id].update(fields)
    coll = collection("jobs")
    if coll is not None:
        try:
            coll.update_one({"dataset_id": dataset_id}, {"$set": fields})
        except Exception:
            pass
    return _memory_jobs.get(dataset_id)


def get_job(dataset_id: str) -> dict[str, Any] | None:
    coll = collection("jobs")
    if coll is not None:
        try:
            doc = coll.find_one({"dataset_id": dataset_id})
            if doc:
                doc.pop("_id", None)
                return doc
        except Exception:
            pass
    return _memory_jobs.get(dataset_id)


def publish_event(dataset_id: str, event: dict[str, Any]) -> None:
    if dataset_id in _memory_jobs:
        if "events" not in _memory_jobs[dataset_id]:
            _memory_jobs[dataset_id]["events"] = []
        _memory_jobs[dataset_id]["events"].append(event)
    coll = collection("jobs")
    if coll is not None:
        try:
            coll.update_one({"dataset_id": dataset_id}, {"$push": {"events": event}})
        except Exception:
            pass


async def subscribe(dataset_id: str) -> AsyncIterator[dict[str, Any]]:
    """Yield decoded progress events for a dataset by polling in-memory / MongoDB."""
    last_count = 0
    while True:
        job = await asyncio.to_thread(get_job, dataset_id)
        if job and "events" in job:
            events = job["events"]
            for i in range(last_count, len(events)):
                yield events[i]
            last_count = len(events)
            if job.get("status") in ("completed", "failed"):
                break
        await asyncio.sleep(0.5)
