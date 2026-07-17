"""Contracts shared by jurisdiction-specific ingestion packages."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from typing import Any, Protocol

from app.ingest.base import NormalizedUpdate

Payload = Mapping[str, Any] | NormalizedUpdate
Fetcher = Callable[[], AsyncIterator[Payload]]


def normalize_payload(
    payload: Payload, *, default_source: str, default_branch: str
) -> NormalizedUpdate:
    if isinstance(payload, NormalizedUpdate):
        return payload
    values = {
        "external_id": str(payload["external_id"]),
        "source": str(payload.get("source", default_source)),
        "branch": str(payload.get("branch", default_branch)),
        "headline": str(payload.get("headline", "")),
        "summary": str(payload.get("summary", "")),
        "full_text": str(payload.get("full_text", "")),
        "url": str(payload.get("url", "")),
        "tags": list(payload.get("tags", [])),
        "metadata": dict(payload.get("metadata", {})),
        "entities": list(payload.get("entities", [])),
    }
    if payload.get("published_at") is not None:
        values["published_at"] = payload["published_at"]
    return NormalizedUpdate(**values)


class JurisdictionPackage(Protocol):
    """Small adapter seam for a source/jurisdiction package."""

    key: str
    label: str

    async def fetch(self) -> AsyncIterator[Payload]: ...

    def normalize(self, payload: Payload) -> NormalizedUpdate: ...

    def persist(self, updates: list[NormalizedUpdate]) -> list[NormalizedUpdate]: ...
