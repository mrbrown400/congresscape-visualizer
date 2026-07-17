"""Federal jurisdiction package backed by the existing Congress connector."""
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ingest.base import NormalizedUpdate
from app.ingest.congress import fetch_house_and_senate_updates

from .contracts import Fetcher, Payload, normalize_payload


@dataclass(slots=True)
class FederalPackage:
    key: str = "federal"
    label: str = "Federal Congress"
    fetcher: Fetcher = fetch_house_and_senate_updates

    async def fetch(self) -> AsyncIterator[Payload]:
        async for update in self.fetcher():
            yield update

    def normalize(self, payload: Payload) -> NormalizedUpdate:
        return normalize_payload(
            payload,
            default_source="congress.gov",
            default_branch="legislative",
            default_jurisdiction="federal",
        )

    def persist(self, updates: list[NormalizedUpdate]) -> list[NormalizedUpdate]:
        return updates
