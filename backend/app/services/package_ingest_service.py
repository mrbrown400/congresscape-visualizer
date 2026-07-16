"""Application service for fetching through an enabled package registry."""
from __future__ import annotations

from app.ingest.base import NormalizedUpdate
from app.ingest.packages import PackageRegistry


class PackageIngestService:
    def __init__(self, registry: PackageRegistry) -> None:
        self.registry = registry

    async def fetch_and_normalize(self, package_key: str) -> list[NormalizedUpdate]:
        package = self.registry.get(package_key)
        updates = [package.normalize(payload) async for payload in package.fetch()]
        return package.persist(updates)
