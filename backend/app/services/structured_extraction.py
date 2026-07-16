"""Deterministic extraction of source fields and ordered lifecycle events."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

SUPPORTED_FIELDS = (
    "report_identifier",
    "requested_action",
    "recommendation",
    "date",
    "amount",
    "project",
    "vendor",
    "location",
    "body",
    "final_outcome",
)


@dataclass(frozen=True, slots=True)
class StructuredClaim:
    canonical_id: str
    claim_type: str
    value: Any
    source_location: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    canonical_id: str
    event_type: str
    occurred_at: datetime | None
    sequence: int
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    claims: tuple[StructuredClaim, ...]
    lifecycle: tuple[LifecycleEvent, ...]


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class StructuredFieldExtractor:
    """Extract only fields with explicit source support; never infer missing values."""

    def extract(self, payload: Mapping[str, Any]) -> ExtractionResult:
        subject_id = str(payload.get("canonical_id") or payload.get("native_id") or "source-record")
        fields = payload.get("fields", {})
        source_location = payload.get("source_location", {})
        claims = tuple(
            StructuredClaim(
                canonical_id=f"{subject_id}:claim:{field}",
                claim_type=field,
                value=value,
                source_location=dict(source_location),
            )
            for field in SUPPORTED_FIELDS
            if isinstance(fields, Mapping) and (value := fields.get(field)) not in (None, "", [])
        )
        lifecycle = tuple(
            sorted(
                (
                    LifecycleEvent(
                        canonical_id=str(event.get("canonical_id") or f"{subject_id}:event:{index}"),
                        event_type=str(event.get("event_type") or "observed"),
                        occurred_at=_as_datetime(event.get("occurred_at")),
                        sequence=int(event.get("sequence", index)),
                        metadata=dict(event.get("metadata", {})),
                    )
                    for index, event in enumerate(payload.get("lifecycle_events", []))
                    if isinstance(event, Mapping)
                ),
                key=lambda event: (event.occurred_at is None, event.occurred_at or datetime.max, event.sequence),
            )
        )
        return ExtractionResult(claims=claims, lifecycle=lifecycle)
