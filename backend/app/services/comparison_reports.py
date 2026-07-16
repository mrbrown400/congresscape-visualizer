"""Source-linked before/after reports with explicit evidence coverage states."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.change_detection import ChangeReport, ChangeUnit


@dataclass(frozen=True, slots=True)
class EvidenceLabel:
    state: str
    text: str
    source_urls: tuple[str, ...]
    coverage_start: str | None
    coverage_end: str | None
    stage: str


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    before_snapshot_id: str
    after_snapshot_id: str
    changes: tuple[ChangeUnit, ...]
    summary: str
    evidence: EvidenceLabel


def _evidence_state(
    source_urls: tuple[str, ...],
    *,
    conflicting: bool,
    extraction_status: tuple[str, ...],
) -> tuple[str, str]:
    if conflicting:
        return "conflicting", "Sources disagree; retain both records for review."
    if not source_urls:
        return "missing", "No source link is available for this comparison."
    if any(status not in {"complete", "available"} for status in extraction_status):
        return "partial", "Source coverage is incomplete for this comparison."
    return "complete", "Comparison is backed by available source records."


def build_comparison_report(
    before: dict[str, Any],
    after: dict[str, Any],
    change_report: ChangeReport,
    *,
    stage: str,
    conflicting: bool = False,
) -> ComparisonReport:
    source_urls = tuple(dict.fromkeys((*before.get("source_urls", []), *after.get("source_urls", []))))
    statuses = (str(before.get("extraction_status", "complete")), str(after.get("extraction_status", "complete")))
    state, text = _evidence_state(source_urls, conflicting=conflicting, extraction_status=statuses)
    evidence = EvidenceLabel(
        state=state,
        text=text,
        source_urls=source_urls,
        coverage_start=before.get("coverage_start") or after.get("coverage_start"),
        coverage_end=after.get("coverage_end") or before.get("coverage_end"),
        stage=stage,
    )
    return ComparisonReport(
        before_snapshot_id=str(before["snapshot_id"]),
        after_snapshot_id=str(after["snapshot_id"]),
        changes=change_report.changes,
        summary=change_report.summary,
        evidence=evidence,
    )
