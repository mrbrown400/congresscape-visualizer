"""Page, table, paragraph, and claim comparison with materiality scoring."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

LEVEL_WEIGHTS = {"page": 0.3, "paragraph": 0.5, "table": 0.8, "claim": 1.0}


@dataclass(frozen=True, slots=True)
class ChangeUnit:
    level: str
    key: str
    classification: str
    before: Any
    after: Any
    materiality: float


@dataclass(frozen=True, slots=True)
class ChangeReport:
    changes: tuple[ChangeUnit, ...]
    material_changes: tuple[ChangeUnit, ...]
    summary: str
    alert_candidate: bool


def _normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _snapshot_units(snapshot: dict[str, Any]) -> dict[tuple[str, str], Any]:
    units: dict[tuple[str, str], Any] = {}
    for page in snapshot.get("pages", []):
        page_number = page.get("page")
        page_key = f"page:{page_number}"
        units[("page", page_key)] = page.get("text", "")
        for index, paragraph in enumerate(str(page.get("text", "")).split("\n\n")):
            units[("paragraph", f"{page_key}:paragraph:{index}")] = paragraph
        for index, table in enumerate(page.get("tables", [])):
            units[("table", f"{page_key}:table:{index}")] = table
    for claim in snapshot.get("claims", []):
        claim_id = claim.get("canonical_id") or claim.get("id")
        if claim_id:
            units[("claim", f"claim:{claim_id}")] = claim.get("value")
    return units


def compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> ChangeReport:
    before_units = _snapshot_units(before)
    after_units = _snapshot_units(after)
    changes: list[ChangeUnit] = []
    for level, key in sorted(set(before_units) | set(after_units)):
        old = before_units.get((level, key))
        new = after_units.get((level, key))
        if _normalized(old) == _normalized(new):
            continue
        classification = "added" if old is None else "removed" if new is None else "changed"
        changes.append(ChangeUnit(level, key, classification, old, new, LEVEL_WEIGHTS[level]))
    material = tuple(change for change in changes if change.materiality >= LEVEL_WEIGHTS["paragraph"])
    source_url = after.get("source_url") or before.get("source_url") or "source document"
    if not material:
        summary = "No material source changes detected."
    else:
        summary = f"{len(material)} material source change(s) detected in {source_url}."
    return ChangeReport(tuple(changes), material, summary, bool(material))
