from datetime import datetime, timezone

from app.services.backup_restore import build_manifest, verify_restore


def test_backup_manifest_round_trip_checks_schema_counts_and_rows() -> None:
    schema = {"government_updates": ["id", "headline"], "source_links": ["id", "url"]}
    rows = {"government_updates": [{"id": 1, "headline": "A"}], "source_links": [{"id": 2, "url": "https://official"}]}
    manifest = build_manifest("snapshot-1", schema, rows, created_at=datetime(2026, 7, 16, tzinfo=timezone.utc))
    result = verify_restore(manifest, schema, {"source_links": rows["source_links"], "government_updates": rows["government_updates"]})
    assert result.passed
    assert result.failures == ()


def test_backup_restore_rejects_schema_or_data_drift() -> None:
    schema = {"government_updates": ["id", "headline"]}
    rows = {"government_updates": [{"id": 1, "headline": "A"}]}
    manifest = build_manifest("snapshot-1", schema, rows)
    result = verify_restore(manifest, {"government_updates": ["id", "headline", "source"]}, {"government_updates": [{"id": 1, "headline": "Changed"}]})
    assert not result.passed
    assert result.failures == ("schema", "rows")
