"""CyberShield SSE streaming endpoint for real-time anomaly detection.

GET /api/cyber/stream   — Server-Sent Events stream of scored network logs
GET /api/cyber/status   — Health / stats of the cyber stream
"""

from __future__ import annotations

import asyncio
import csv
import uuid
from datetime import UTC, datetime
from pathlib import Path

import geoip2.database
import geoip2.errors
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.models.cyber_schemas import CyberStreamStatus, ScoredRow, ThreatLevel
from app.services.anomaly_scorer import AnomalyScorer
from app.services.ring_buffer import RingBuffer

router = APIRouter(prefix="/api/cyber", tags=["cybershield"])

# ── Globals ─────────────────────────────────────────────────────────────────
_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "sample-data"
    / "network_traffic.csv"
)
_MMDB_PATH = Path(__file__).resolve().parent.parent.parent / "GeoLite2-City.mmdb"
_scorer: AnomalyScorer | None = None
_geo_reader = None
_ring_buffer = RingBuffer(maxsize=1000)
_total_events = 0
_active_connections = 0


def _get_scorer() -> AnomalyScorer:
    """Lazy-initialise the anomaly scorer on first request."""
    global _scorer
    if _scorer is None:
        _scorer = AnomalyScorer(csv_path=_DATA_PATH)
    return _scorer


def _get_geo_reader():
    """Lazy-initialise the GeoIP reader."""
    global _geo_reader
    if _geo_reader is None and _MMDB_PATH.exists():
        _geo_reader = geoip2.database.Reader(str(_MMDB_PATH))
    return _geo_reader


def _load_csv_rows() -> list[dict]:
    """Load all rows from the sample CSV."""
    with open(_DATA_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


async def _sse_generator(
    request: Request,
    rows_per_sec: float,
):
    """Async generator that replays CSV rows as SSE events."""
    global _total_events, _active_connections
    _active_connections += 1

    try:
        scorer = _get_scorer()
        rows = _load_csv_rows()
        delay = 1.0 / max(0.1, rows_per_sec)
        row_index = 0

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            row = rows[row_index % len(rows)]

            # Convert numeric fields from CSV strings
            numeric_fields = [
                "src_port",
                "dst_port",
                "bytes_sent",
                "bytes_received",
                "duration_ms",
                "packet_count",
                "is_encrypted",
            ]
            for field in numeric_fields:
                if field in row:
                    row[field] = int(row[field])

            # Score the row
            result = scorer.score(row)

            # GeoIP lookup
            src_lat = None
            src_lon = None
            geo_reader = _get_geo_reader()
            src_ip = row.get("src_ip", "")
            if geo_reader and src_ip:
                try:
                    match = geo_reader.city(src_ip)
                    src_lat = match.location.latitude
                    src_lon = match.location.longitude
                except geoip2.errors.AddressNotFoundError:
                    pass

            # Build the SSE payload
            scored = ScoredRow(
                row_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(UTC).isoformat(),
                anomaly_score=result["anomaly_score"],
                threat_level=ThreatLevel(result["threat_level"]),
                top_features=result["top_features"],
                raw={
                    "timestamp": row.get("timestamp", ""),
                    "src_ip": src_ip,
                    "dst_ip": row.get("dst_ip", ""),
                    "src_port": int(row.get("src_port", 0)),
                    "dst_port": int(row.get("dst_port", 0)),
                    "protocol": row.get("protocol", ""),
                    "bytes_sent": int(row.get("bytes_sent", 0)),
                    "bytes_received": int(row.get("bytes_received", 0)),
                    "duration_ms": int(row.get("duration_ms", 0)),
                    "packet_count": int(row.get("packet_count", 0)),
                    "tcp_flags": row.get("tcp_flags", ""),
                    "is_encrypted": int(row.get("is_encrypted", 0)),
                    "src_lat": src_lat,
                    "src_lon": src_lon,
                },
            )

            payload = scored.model_dump_json()
            _ring_buffer.push(payload)
            _total_events += 1

            yield f"data: {payload}\n\n"

            row_index += 1
            await asyncio.sleep(delay)

    finally:
        _active_connections -= 1


@router.get("/stream")
async def cyber_stream(
    request: Request,
    rows_per_sec: float = Query(
        default=10.0, ge=0.1, le=100.0, description="Replay speed"
    ),
):
    """SSE endpoint streaming scored network log rows in real time."""
    return StreamingResponse(
        _sse_generator(request, rows_per_sec),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status", response_model=CyberStreamStatus)
async def cyber_status():
    """Health and statistics for the CyberShield stream."""
    return CyberStreamStatus(
        scorer_ready=_scorer is not None and _scorer.ready,
        buffer_size=_ring_buffer.size,
        buffer_capacity=_ring_buffer.capacity,
        total_events_emitted=_total_events,
        active_connections=_active_connections,
    )
