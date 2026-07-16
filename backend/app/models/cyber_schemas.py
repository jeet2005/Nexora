"""Pydantic models for CyberShield real-time anomaly detection."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ThreatLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NetworkLogRow(BaseModel):
    """Raw network log fields from the CSV."""

    timestamp: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes_sent: int
    bytes_received: int
    duration_ms: int
    packet_count: int
    tcp_flags: str
    is_encrypted: int
    src_lat: float | None = None
    src_lon: float | None = None


class ScoredRow(BaseModel):
    """A single SSE event payload — scored network log row."""

    row_id: str = Field(description="Unique event identifier")
    timestamp: str = Field(description="ISO-8601 timestamp of the event")
    anomaly_score: float = Field(
        ge=0.0, le=1.0, description="Combined anomaly score")
    threat_level: ThreatLevel
    top_features: list[str] = Field(
        description="Top 3 features contributing to anomaly score"
    )
    raw: NetworkLogRow = Field(description="Original network log fields")


class CyberStreamStatus(BaseModel):
    """Health / status response for the cyber stream."""

    scorer_ready: bool
    buffer_size: int
    buffer_capacity: int
    total_events_emitted: int
    active_connections: int
