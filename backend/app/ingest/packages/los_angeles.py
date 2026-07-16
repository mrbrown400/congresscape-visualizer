"""Concrete Los Angeles source packages with deterministic normalization."""
from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any

from app.ingest.base import NormalizedUpdate

from .contracts import PackageCapabilities, Payload


@dataclass(slots=True)
class LosAngelesPackage:
    """Adapter for one named LA source, such as Metro or the City."""

    key: str
    label: str
    fixture: Mapping[str, Any] | None = None
    capabilities: PackageCapabilities = PackageCapabilities()

    async def fetch(self) -> AsyncIterator[Payload]:
        if self.fixture is not None:
            yield self.fixture

    def normalize(self, payload: Payload) -> NormalizedUpdate:
        if isinstance(payload, NormalizedUpdate):
            return payload
        return NormalizedUpdate(
            external_id=str(payload["external_id"]),
            source=str(payload.get("source", self.key)),
            branch=str(payload.get("branch", "agency")),
            headline=str(payload.get("headline", "")),
            summary=str(payload.get("summary", "")),
            full_text=str(payload.get("full_text", "")),
            published_at=payload.get("published_at") or NormalizedUpdate.__dataclass_fields__["published_at"].default_factory(),
            url=str(payload.get("url", "")),
            tags=list(payload.get("tags", [])),
            metadata=dict(payload.get("metadata", {})),
            entities=list(payload.get("entities", [])),
        )

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


def build_los_angeles_packages() -> tuple[LosAngelesPackage, ...]:
    return (
        LosAngelesPackage("la.city", "City of Los Angeles"),
        LosAngelesPackage("la.metro", "Los Angeles County Metropolitan Transportation Authority"),
    )
