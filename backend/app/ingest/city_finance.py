"""Normalized, network-free seams for the six current City Controller datasets."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

DATASETS = {
    "pggv-e4fn": "payment",
    "5662-zu2k": "vendor",
    "uyzw-yi8n": "expenditure",
    "hfus-a659": "revenue",
    "ej7u-di9z": "balance",
    "ebs9-fdwv": "authorization",
}


@dataclass(frozen=True, slots=True)
class FinanceRecord:
    dataset_id: str
    record_type: str
    source_key: str | None
    amount: Decimal | None
    amount_state: str
    vendor_id: str | None
    vendor_name: str | None
    rows_updated_at: datetime | None
    stale_metadata: bool
    raw: Mapping[str, Any]


def paginate_rows(rows: Iterable[Mapping[str, Any]], page_size: int = 500) -> tuple[tuple[Mapping[str, Any], ...], ...]:
    materialized = tuple(rows)
    return tuple(tuple(materialized[index : index + page_size]) for index in range(0, len(materialized), page_size))


def _updated_at(metadata: Mapping[str, Any]) -> datetime | None:
    value = metadata.get("rowsUpdatedAt")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _amount(row: Mapping[str, Any]) -> tuple[Decimal | None, str]:
    value = row.get("amount") or row.get("Amount") or row.get("payment_amount")
    if value in (None, ""):
        return None, "missing"
    try:
        return Decimal(str(value)), "present"
    except (InvalidOperation, ValueError):
        return None, "invalid"


def _source_key(dataset_id: str, row: Mapping[str, Any]) -> str | None:
    if dataset_id == "ebs9-fdwv":
        return str(row["row_id"]) if row.get("row_id") else None
    if dataset_id == "pggv-e4fn":
        parts = [row.get(field) for field in ("data_source", "transaction_id", "invoice", "purchase_order")]
        return ":".join(str(part or "missing") for part in parts)
    for field in ("row_id", "id", "vendor_id", "record_id"):
        if row.get(field):
            return str(row[field])
    return None


def normalize_rows(
    dataset_id: str, rows: Iterable[Mapping[str, Any]], metadata: Mapping[str, Any]
) -> tuple[FinanceRecord, ...]:
    if dataset_id not in DATASETS:
        raise ValueError(f"Unsupported City Controller dataset: {dataset_id}")
    updated_at = _updated_at(metadata)
    stale = updated_at is None or updated_at < datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)
    return tuple(
        FinanceRecord(
            dataset_id=dataset_id,
            record_type=DATASETS[dataset_id],
            source_key=_source_key(dataset_id, row),
            amount=_amount(row)[0],
            amount_state=_amount(row)[1],
            vendor_id=str(row["vendor_id"]) if row.get("vendor_id") else None,
            vendor_name=str(row["vendor_name"]) if row.get("vendor_name") else None,
            rows_updated_at=updated_at,
            stale_metadata=stale,
            raw=dict(row),
        )
        for row in rows
    )


def reconciliation_groups(records: Iterable[FinanceRecord]) -> dict[str, tuple[FinanceRecord, ...]]:
    groups: dict[str, list[FinanceRecord]] = {}
    for record in records:
        groups.setdefault(record.record_type, []).append(record)
    return {record_type: tuple(values) for record_type, values in groups.items()}
