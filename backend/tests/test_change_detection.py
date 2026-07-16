from __future__ import annotations

from app.services.change_detection import compare_snapshots


def test_formatting_only_changes_are_suppressed() -> None:
    before = {"pages": [{"page": 1, "text": "Adopt the plan", "tables": []}]}
    after = {"pages": [{"page": 1, "text": "  Adopt   the plan  ", "tables": []}]}

    report = compare_snapshots(before, after)

    assert report.changes == ()
    assert report.alert_candidate is False


def test_claim_and_table_changes_are_material_and_source_linked() -> None:
    before = {
        "source_url": "https://boardagendas.metro.net/report/1",
        "pages": [{"page": 1, "text": "Recommendation", "tables": [["Amount", "10"]]}],
        "claims": [{"canonical_id": "claim:amount", "value": "10"}],
    }
    after = {
        "source_url": "https://boardagendas.metro.net/report/1",
        "pages": [{"page": 1, "text": "Recommendation", "tables": [["Amount", "20"]]}],
        "claims": [{"canonical_id": "claim:amount", "value": "20"}],
    }

    report = compare_snapshots(before, after)

    assert {change.level for change in report.material_changes} == {"table", "claim"}
    assert report.alert_candidate is True
    assert "https://boardagendas.metro.net/report/1" in report.summary


def test_added_and_removed_units_are_classified() -> None:
    report = compare_snapshots(
        {"pages": [{"page": 1, "text": "Old", "tables": []}]},
        {"pages": [{"page": 1, "text": "New", "tables": []}, {"page": 2, "text": "Added", "tables": []}]},
    )

    assert {change.classification for change in report.changes} == {"changed", "added"}
