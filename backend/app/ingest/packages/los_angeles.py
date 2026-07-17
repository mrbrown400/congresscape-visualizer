"""Concrete Los Angeles source packages with deterministic normalization."""
from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any

from app.ingest.base import NormalizedUpdate

from .contracts import Payload, normalize_payload


@dataclass(slots=True)
class LosAngelesPackage:
    """Adapter for one named LA source, such as Metro or the City."""

    key: str
    label: str
    fixture: Mapping[str, Any] | None = None

    async def fetch(self) -> AsyncIterator[Payload]:
        if self.fixture is not None:
            yield self.fixture

    def normalize(self, payload: Payload) -> NormalizedUpdate:
        return normalize_payload(
            payload,
            default_source=self.key,
            default_branch="agency",
            default_jurisdiction=self.key,
        )

    def persist(self, updates: list[NormalizedUpdate]) -> list[NormalizedUpdate]:
        return updates



def build_los_angeles_packages() -> tuple[LosAngelesPackage, ...]:
    return (
        LosAngelesPackage("la.city", "City of Los Angeles"),
        LosAngelesPackage("la.metro", "Los Angeles County Metropolitan Transportation Authority"),
    )
