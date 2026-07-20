"""MongoDB-backed job status for background training jobs."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.services.persistence_service import collection


def set_job(dataset_id: str, job: dict[str, Any]) -> None:
    coll = collection("jobs")
    if coll is not None:
        if "events" not in job:
            job["events"] = []
        coll.update_one({"dataset_id": dataset_id}, {"$set": job}, upsert=True)


def update_job(dataset_id: str, **fields: Any) -> dict[str, Any] | None:
    coll = collection("jobs")
    if coll is not None:
        coll.update_one({"dataset_id": dataset_id}, {"$set": fields})
        return get_job(dataset_id)
    return None


def get_job(dataset_id: str) -> dict[str, Any] | None:
    coll = collection("jobs")
    if coll is not None:
        doc = coll.find_one({"dataset_id": dataset_id})
        if doc:
            doc.pop("_id", None)
            return doc
    return None


def publish_event(dataset_id: str, event: dict[str, Any]) -> None:
    coll = collection("jobs")
    if coll is not None:
        coll.update_one({"dataset_id": dataset_id}, {"$push": {"events": event}})


async def subscribe(dataset_id: str) -> AsyncIterator[dict[str, Any]]:
    """Yield decoded progress events for a dataset by polling MongoDB."""
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
        await asyncio.sleep(1.0)
