"""Federal jurisdiction package backed by the existing Congress connector."""
from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any

from app.ingest.base import NormalizedUpdate
from app.ingest.congress import fetch_house_and_senate_updates

from .contracts import PackageCapabilities, Payload


def _normalize_payload(payload: Payload) -> NormalizedUpdate:
    if isinstance(payload, NormalizedUpdate):
        return payload
    return NormalizedUpdate(
        external_id=str(payload["external_id"]),
        source=str(payload.get("source", "congress.gov")),
        branch=str(payload.get("branch", "legislative")),
        headline=str(payload.get("headline", "")),
        summary=str(payload.get("summary", "")),
        full_text=str(payload.get("full_text", "")),
        url=str(payload.get("url", "")),
        tags=list(payload.get("tags", [])),
        metadata=dict(payload.get("metadata", {})),
        entities=list(payload.get("entities", [])),
    )


@dataclass(slots=True)
class FederalPackage:
    key: str = "federal"
    label: str = "Federal Congress"
    fetcher: Any = fetch_house_and_senate_updates
    capabilities: PackageCapabilities = PackageCapabilities()

    async def fetch(self) -> AsyncIterator[Payload]:
        async for update in self.fetcher():
            yield update

    def normalize(self, payload: Payload) -> NormalizedUpdate:
        return _normalize_payload(payload)

    def persist(self, updates: list[NormalizedUpdate]) -> list[NormalizedUpdate]:
        return updates

    def lifecycle_mapping(self, payload: Payload) -> Mapping[str, Any]:
        return payload.get("lifecycle", {}) if isinstance(payload, Mapping) else {}

    def documents(self, payload: Payload) -> list[Mapping[str, Any]]:
        return list(payload.get("documents", [])) if isinstance(payload, Mapping) else []

    def entities(self, payload: Payload) -> list[Mapping[str, Any]]:
        return list(payload.get("entities", [])) if isinstance(payload, Mapping) else []

    def money_context(self, payload: Payload) -> Mapping[str, Any]:
        return payload.get("money_context", {}) if isinstance(payload, Mapping) else {}

    def ranking(self, payload: Payload) -> Mapping[str, Any]:
        return payload.get("ranking", {}) if isinstance(payload, Mapping) else {}

    def diagnostics(self, payload: Payload) -> Mapping[str, Any]:
        return payload.get("diagnostics", {}) if isinstance(payload, Mapping) else {}

    def alerts(self, payload: Payload) -> list[Mapping[str, Any]]:
        return list(payload.get("alerts", [])) if isinstance(payload, Mapping) else []
