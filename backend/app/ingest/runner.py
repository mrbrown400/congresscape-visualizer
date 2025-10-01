"""Ingestion orchestration utilities."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterable

from app.ingest.base import NormalizedUpdate


async def drain(source: AsyncIterator[NormalizedUpdate]) -> list[NormalizedUpdate]:
    """Read all updates from an async iterator."""

    results: list[NormalizedUpdate] = []
    async for item in source:
        results.append(item)
    return results


async def run_ingestion(tasks: Iterable[Callable[[], AsyncIterator[NormalizedUpdate]]]) -> list[NormalizedUpdate]:
    """Run multiple async ingestion generators and merge their results."""

    aggregated: list[NormalizedUpdate] = []
    for factory in tasks:
        aggregated.extend(await drain(factory()))
    return aggregated
