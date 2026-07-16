"""Optional MongoDB persistence with a local-file fallback.

The existing app is intentionally file-first for local development. These helpers let
production deployments mirror structured records to MongoDB Atlas when configured,
without making MongoDB mandatory for smoke tests or offline demos.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)
_client_instance = None


def _client():
    global _client_instance
    if _client_instance is not None:
        return _client_instance

    if settings.persistence_backend.lower() != "mongodb" or not settings.mongodb_uri:
        logger.warning(
            "MongoDB persistence is disabled or MONGODB_URI is not configured."
        )
        return None

    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        logger.error(
            "PyMongo is not installed; MongoDB persistence is unavailable.")
        return None

    for attempt in range(3):
        try:
            client = MongoClient(settings.mongodb_uri,
                                 serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            _client_instance = client
            return client
        except PyMongoError as exc:
            logger.error(
                "MongoDB connection failed on attempt %d: %s",
                attempt + 1,
                exc,
            )
            if attempt < 2:
                time.sleep(1)
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
