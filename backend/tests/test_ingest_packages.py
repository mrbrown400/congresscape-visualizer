from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ingest.packages import (
    FederalPackage,
    LosAngelesPackage,
    PackageNotEnabledError,
    PackageRegistry,
    build_los_angeles_packages,
)


FIXTURE = Path(__file__).parent / "fixtures" / "los_angeles" / "policy_item.json"


def test_registry_requires_explicit_enablement() -> None:
    packages = (FederalPackage(), *build_los_angeles_packages())
    registry = PackageRegistry(packages, enabled=("federal", "la.metro"))

    assert registry.keys() == ("federal", "la.metro")
    assert registry.get("la.metro").key == "la.metro"
    with pytest.raises(PackageNotEnabledError, match="not enabled"):
        registry.get("la.city")
    with pytest.raises(PackageNotEnabledError, match="not enabled"):
        registry.get("los_angeles")


@pytest.mark.asyncio
async def test_los_angeles_fixture_normalizes_deterministically() -> None:
    payload = json.loads(FIXTURE.read_text())
    package = LosAngelesPackage(
        "la.metro",
        "Los Angeles County Metropolitan Transportation Authority",
        fixture=payload,
    )
    registry = PackageRegistry((package,), enabled=(package.key,))

    selected = registry.get(package.key)
    updates = [selected.normalize(payload) async for payload in selected.fetch()]
    updates = selected.persist(updates)

    assert len(updates) == 1
    assert updates[0].external_id == "metro-board-2026-001"
    assert updates[0].source == "la.metro"
    assert updates[0].branch == "agency"
    assert updates[0].metadata["agency"].startswith("Los Angeles")
