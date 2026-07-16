"""Append-only operational snapshots and transparent record comparisons."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class DatasetSnapshot:
    snapshot_id: str
    source_url: str
    retrieved_at: datetime
    byte_hash: str
    source_kind: str
    metadata: dict[str, Any]
    freshness_state: str = "unknown"


@dataclass(frozen=True, slots=True)
class SnapshotComparison:
    before_snapshot_id: str
    after_snapshot_id: str
    method: str
    crs: str | None
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, DatasetSnapshot] = {}

    def add(self, snapshot: DatasetSnapshot) -> DatasetSnapshot:
        self._snapshots.setdefault(snapshot.snapshot_id, snapshot)
        return self._snapshots[snapshot.snapshot_id]

    def all(self) -> tuple[DatasetSnapshot, ...]:
        return tuple(self._snapshots.values())


def make_snapshot(
    *, source_url: str, retrieved_at: datetime, content: bytes, source_kind: str, metadata: dict[str, Any], freshness_state: str = "unknown"
) -> DatasetSnapshot:
    byte_hash = hashlib.sha256(content).hexdigest()
    identity = json.dumps(
        {"source_url": source_url, "retrieved_at": retrieved_at.isoformat(), "byte_hash": byte_hash},
        sort_keys=True,
    ).encode()
    return DatasetSnapshot(
        snapshot_id=hashlib.sha256(identity).hexdigest(),
        source_url=source_url,
        retrieved_at=retrieved_at,
        byte_hash=byte_hash,
        source_kind=source_kind,
        metadata=dict(metadata),
        freshness_state=freshness_state,
    )


def compare_records(
    before: DatasetSnapshot,
    after: DatasetSnapshot,
    before_records: Iterable[dict[str, Any]],
    after_records: Iterable[dict[str, Any]],
    *,
    identifier: str,
    crs: str | None = None,
) -> SnapshotComparison:
    old = {str(record[identifier]): record for record in before_records if record.get(identifier) is not None}
    new = {str(record[identifier]): record for record in after_records if record.get(identifier) is not None}
    return SnapshotComparison(
        before_snapshot_id=before.snapshot_id,
        after_snapshot_id=after.snapshot_id,
        method=f"exact:{identifier}",
        crs=crs,
        added=tuple(sorted(set(new) - set(old))),
        removed=tuple(sorted(set(old) - set(new))),
        changed=tuple(sorted(key for key in set(old) & set(new) if old[key] != new[key])),
    )
