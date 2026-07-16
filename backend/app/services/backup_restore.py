"""Deterministic backup manifest and restore verification primitives."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class BackupManifest:
    snapshot_id: str
    schema_hash: str
    table_counts: dict[str, int]
    row_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RestoreVerification:
    passed: bool
    schema_match: bool
    counts_match: bool
    rows_match: bool
    failures: tuple[str, ...] = ()


def build_manifest(snapshot_id: str, schema: dict[str, list[str]], rows: dict[str, list[dict[str, Any]]], *, created_at: datetime | None = None) -> BackupManifest:
    schema_hash = _digest(schema)
    row_hash = _digest({table: sorted(values, key=lambda value: json.dumps(value, sort_keys=True)) for table, values in rows.items()})
    return BackupManifest(snapshot_id, schema_hash, {table: len(values) for table, values in rows.items()}, row_hash, created_at or datetime.now(timezone.utc))


def verify_restore(manifest: BackupManifest, schema: dict[str, list[str]], rows: dict[str, list[dict[str, Any]]]) -> RestoreVerification:
    schema_match = manifest.schema_hash == _digest(schema)
    counts = {table: len(values) for table, values in rows.items()}
    counts_match = manifest.table_counts == counts
    row_hash = _digest({table: sorted(values, key=lambda value: json.dumps(value, sort_keys=True)) for table, values in rows.items()})
    rows_match = manifest.row_hash == row_hash
    failures = tuple(
        label for label, passed in (("schema", schema_match), ("table_counts", counts_match), ("rows", rows_match)) if not passed
    )
    return RestoreVerification(not failures, schema_match, counts_match, rows_match, failures)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
