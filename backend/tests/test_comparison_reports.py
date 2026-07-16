from __future__ import annotations

from app.services.change_detection import compare_snapshots
from app.services.comparison_reports import build_comparison_report


def _report(before: dict, after: dict, **kwargs):
    changes = compare_snapshots(before, after)
    return build_comparison_report(before, after, changes, stage="final_action", **kwargs)


def test_complete_report_has_sources_dates_and_stage() -> None:
    report = _report(
        {"snapshot_id": "before", "source_urls": ["https://official/before"], "coverage_start": "2026-01-01"},
        {"snapshot_id": "after", "source_urls": ["https://official/after"], "coverage_end": "2026-02-01"},
    )

    assert report.evidence.state == "complete"
    assert report.evidence.source_urls == ("https://official/before", "https://official/after")
    assert report.evidence.coverage_start == "2026-01-01"
    assert report.evidence.coverage_end == "2026-02-01"
    assert report.evidence.stage == "final_action"


def test_partial_missing_and_conflicting_labels_are_explicit() -> None:
    partial = _report(
        {"snapshot_id": "before", "source_urls": ["https://official/before"], "extraction_status": "complete"},
        {"snapshot_id": "after", "source_urls": ["https://official/after"], "extraction_status": "unsupported"},
    )
    missing = _report({"snapshot_id": "before"}, {"snapshot_id": "after"})
    conflicting = _report(
        {"snapshot_id": "before", "source_urls": ["https://official/before"]},
        {"snapshot_id": "after", "source_urls": ["https://official/after"]},
        conflicting=True,
    )

    assert partial.evidence.state == "partial"
    assert missing.evidence.state == "missing"
    assert conflicting.evidence.state == "conflicting"
