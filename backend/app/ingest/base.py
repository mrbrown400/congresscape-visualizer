"""Ingestion base classes and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Iterable, Protocol


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class NormalizedUpdate:
    external_id: str
    source: str
    branch: str
    headline: str
    summary: str = ""
    full_text: str = ""
    published_at: datetime = field(default_factory=utcnow)
    event_date: datetime | None = None  # For future events (effective dates, deadlines)
    url: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    entities: list[str] = field(default_factory=list)


class IngestSource(Protocol):
    """Protocol for async ingest implementations."""

    async def fetch(self) -> AsyncIterator[NormalizedUpdate]:
        ...


class SyncIngestSource(Protocol):
    """Protocol for sync generators to be wrapped as async."""

    def fetch(self) -> Iterable[NormalizedUpdate]:
        ...
