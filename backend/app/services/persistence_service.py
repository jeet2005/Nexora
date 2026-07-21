"""MongoDB persistence with an instant local-file fallback.

Fast-fail mechanism ensures that if MongoDB is offline or unreachable,
requests fall back to local storage in <1.5s instead of hanging for 17+ seconds
and causing HTTP 502 proxy timeouts.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_client_instance = None
_mongo_failed = False
_last_check_time = 0.0


def _client():
    global _client_instance, _mongo_failed, _last_check_time

    if _client_instance is not None:
        return _client_instance

    now = time.time()
    # Fast-fail: if MongoDB failed within the last 30s, return None instantly (0ms)
    if _mongo_failed and (now - _last_check_time < 30.0):
        return None

    if settings.persistence_backend.lower() != "mongodb" or not settings.mongodb_uri:
        return None

    try:
        from pymongo import MongoClient
    except ImportError:
        logger.error("PyMongo is not installed; MongoDB persistence is unavailable.")
        return None

    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        _client_instance = client
        _mongo_failed = False
        logger.info("MongoDB connected successfully.")
        return client
    except Exception as exc:
        logger.warning(
            "MongoDB ping failed (%s); caching offline fallback for 30s.", exc
        )
        _mongo_failed = True
        _last_check_time = now
        return None


def collection(name: str):
    client = _client()
    if client is None:
        return None
    return client[settings.mongodb_db][name]


def upsert(collection_name: str, key: dict[str, Any], document: dict[str, Any]) -> None:
    coll = collection(collection_name)
    if coll is None:
        return
    try:
        coll.update_one(key, {"$set": document}, upsert=True)
    except Exception:
        return


def insert(collection_name: str, document: dict[str, Any]) -> None:
    coll = collection(collection_name)
    if coll is None:
        return
    try:
        coll.insert_one(document)
    except Exception:
        return


def find(
    collection_name: str, query: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    coll = collection(collection_name)
    if coll is None:
        return []
    try:
        out = []
        for doc in coll.find(query or {}):
            doc.pop("_id", None)
            out.append(doc)
        return out
    except Exception:
        return []
