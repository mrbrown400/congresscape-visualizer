from __future__ import annotations

from datetime import datetime, timezone

from app.services.operational_snapshots import SnapshotStore, compare_records, make_snapshot


def test_snapshots_are_append_only_and_identical_downloads_deduplicate() -> None:
    kwargs = {
        "source_url": "https://gitlab.com/LACMTA/gtfs_bus/-/raw/master/gtfs_bus.zip",
        "retrieved_at": datetime(2026, 7, 14, tzinfo=timezone.utc),
        "content": b"gtfs",
        "source_kind": "gtfs_static",
        "metadata": {"branch": "master", "commit_sha": "abc", "calendar_range": "2026-01-01/2026-12-31"},
    }
    first = make_snapshot(**kwargs)
    second = make_snapshot(**kwargs)
    store = SnapshotStore()

    assert store.add(first) == first
    assert store.add(second) == first
    assert len(store.all()) == 1


def test_operational_comparison_reports_ids_method_and_crs() -> None:
    before = make_snapshot(
        source_url="https://example.test/gis",
        retrieved_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        content=b"before",
        source_kind="arcgis",
        metadata={"item_id": "item-1", "layer_id": "0"},
    )
    after = make_snapshot(
        source_url="https://example.test/gis",
        retrieved_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        content=b"after",
        source_kind="arcgis",
        metadata={"item_id": "item-1", "layer_id": "0"},
        freshness_state="stale",
    )

    comparison = compare_records(
        before,
        after,
        [{"global_id": "same", "name": "old"}, {"global_id": "removed"}],
        [{"global_id": "same", "name": "new"}, {"global_id": "added"}],
        identifier="global_id",
        crs="EPSG:4326",
    )

    assert comparison.before_snapshot_id == before.snapshot_id
    assert comparison.after_snapshot_id == after.snapshot_id
    assert comparison.method == "exact:global_id"
    assert comparison.crs == "EPSG:4326"
    assert comparison.added == ("added",)
    assert comparison.removed == ("removed",)
    assert comparison.changed == ("same",)
    assert after.freshness_state == "stale"
