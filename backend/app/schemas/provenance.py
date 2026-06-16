"""Schemas for source provenance and freshness diagnostics."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FreshnessStatus = Literal["fresh", "stale", "missing_source", "failed"]
ProvenanceStatus = Literal["available", "missing", "failed"]


class ProvenanceDiagnosticRead(BaseModel):
    """Diagnostic view for a card-producing government update."""

    update_id: int
    external_id: str
    source: str
    headline: str
    published_at: datetime
    source_url: str | None = None
    source_fetched_at: datetime | None = None
    freshness_status: FreshnessStatus
    provenance_status: ProvenanceStatus
    source_trail_count: int
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProvenanceDiagnosticsResponse(BaseModel):
    """Aggregated diagnostics for recent ingested updates."""

    items: list[ProvenanceDiagnosticRead]
    total: int
    counts: dict[str, int]
    stale_after_hours: int
