"""Contracts shared by jurisdiction-specific ingestion packages."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.ingest.base import NormalizedUpdate

Payload = Mapping[str, Any] | NormalizedUpdate
Fetcher = Callable[[], AsyncIterator[Payload]]


@dataclass(frozen=True, slots=True)
class PackageCapabilities:
    """Feature surface exposed by an ingestion package."""

    fetch: bool = True
    normalize: bool = True
    persist: bool = True
    lifecycle_mapping: bool = True
    documents: bool = True
    entities: bool = True
    money_context: bool = True
    ranking: bool = True
    diagnostics: bool = True
    alerts: bool = True


class JurisdictionPackage(Protocol):
    """Small adapter seam for a source/jurisdiction package."""

    key: str
    label: str
    capabilities: PackageCapabilities

    async def fetch(self) -> AsyncIterator[Payload]: ...

    def normalize(self, payload: Payload) -> NormalizedUpdate: ...

    def persist(self, updates: list[NormalizedUpdate]) -> list[NormalizedUpdate]: ...

    def lifecycle_mapping(self, payload: Payload) -> Mapping[str, Any]: ...

    def documents(self, payload: Payload) -> list[Mapping[str, Any]]: ...

    def entities(self, payload: Payload) -> list[Mapping[str, Any]]: ...

    def money_context(self, payload: Payload) -> Mapping[str, Any]: ...

    def ranking(self, payload: Payload) -> Mapping[str, Any]: ...

    def diagnostics(self, payload: Payload) -> Mapping[str, Any]: ...

    def alerts(self, payload: Payload) -> list[Mapping[str, Any]]: ...
