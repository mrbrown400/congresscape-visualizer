"""Stakeholder aliases and coverage diagnostics for county litigation discovery."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Stakeholder:
    canonical_id: str
    name: str
    aliases: tuple[str, ...]
    relationships: tuple[str, ...]
    verification_state: str


@dataclass(frozen=True, slots=True)
class LitigationCoverage:
    courts: tuple[str, ...]
    date_start: str
    date_end: str
    source_completeness: dict[str, str]
    last_successful_retrieval: datetime | None
    blind_spots: tuple[str, ...]


def build_stakeholder_registry(entries: list[dict[str, Any]]) -> tuple[Stakeholder, ...]:
    return tuple(
        Stakeholder(
            canonical_id=str(entry["canonical_id"]),
            name=str(entry["name"]),
            aliases=tuple(str(alias) for alias in entry.get("aliases", [])),
            relationships=tuple(str(value) for value in entry.get("relationships", [])),
            verification_state=str(entry.get("verification_state", "unverified")),
        )
        for entry in entries
    )


def candidate_stakeholders(text: str, registry: tuple[Stakeholder, ...]) -> tuple[Stakeholder, ...]:
    haystack = text.casefold()
    return tuple(
        stakeholder
        for stakeholder in registry
        if stakeholder.verification_state == "verified"
        and any(value.casefold() in haystack for value in (stakeholder.name, *stakeholder.aliases))
    )


def build_coverage_report(
    *,
    courts: list[str],
    date_start: str,
    date_end: str,
    source_completeness: dict[str, str],
    last_successful_retrieval: datetime | None,
    blind_spots: list[str],
) -> LitigationCoverage:
    return LitigationCoverage(
        courts=tuple(courts),
        date_start=date_start,
        date_end=date_end,
        source_completeness=dict(source_completeness),
        last_successful_retrieval=last_successful_retrieval,
        blind_spots=tuple(blind_spots),
    )
