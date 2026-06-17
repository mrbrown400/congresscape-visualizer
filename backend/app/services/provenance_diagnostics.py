"""Provenance metadata stamping and diagnostics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.update import GovernmentUpdate
from app.schemas.provenance import ProvenanceDiagnosticRead, ProvenanceDiagnosticsResponse
from app.services.feed_service import FeedService

DEFAULT_STALE_AFTER_HOURS = 48


def stamp_ingest_provenance(
    metadata: dict[str, Any] | None,
    *,
    source_url: str | None,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    """Add source provenance metadata without overwriting explicit source fields."""

    stamped = dict(metadata or {})
    provenance = _dict(stamped.get("provenance"))
    resolved_url = _string(provenance.get("source_url")) or _string(stamped.get("source_url")) or source_url
    source_fetched_at = (
        _datetime_string(provenance.get("source_fetched_at"))
        or _datetime_string(stamped.get("source_fetched_at"))
        or _first_source_trail_time(stamped)
        or _iso(fetched_at or datetime.now(timezone.utc))
    )

    if resolved_url:
        provenance["source_url"] = resolved_url
    provenance["source_fetched_at"] = source_fetched_at

    failures = _failure_messages(provenance.get("source_failures")) or _failure_messages(stamped.get("source_failures"))
    if failures:
        provenance["source_failures"] = failures

    provenance["freshness_status"] = _static_freshness_status(bool(resolved_url), failures)
    stamped["provenance"] = provenance
    return stamped


class ProvenanceDiagnosticsService:
    """Report stale, failed, or missing source provenance for feed records."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.feed_service = FeedService(session)

    async def list_update_diagnostics(
        self,
        *,
        limit: int = 100,
        stale_after_hours: int = DEFAULT_STALE_AFTER_HOURS,
        now: datetime | None = None,
    ) -> ProvenanceDiagnosticsResponse:
        stmt = select(GovernmentUpdate).order_by(GovernmentUpdate.published_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        diagnostics = [
            self.build_update_diagnostic(update, stale_after_hours=stale_after_hours, now=now)
            for update in result.scalars().all()
        ]
        counts: dict[str, int] = {}
        for diagnostic in diagnostics:
            counts[diagnostic.freshness_status] = counts.get(diagnostic.freshness_status, 0) + 1

        return ProvenanceDiagnosticsResponse(
            items=diagnostics,
            total=len(diagnostics),
            counts=counts,
            stale_after_hours=stale_after_hours,
        )

    def build_update_diagnostic(
        self,
        update: GovernmentUpdate,
        *,
        stale_after_hours: int = DEFAULT_STALE_AFTER_HOURS,
        now: datetime | None = None,
    ) -> ProvenanceDiagnosticRead:
        now = _aware(now or datetime.now(timezone.utc))
        metadata = update.metadata_json or {}
        provenance = _dict(metadata.get("provenance"))
        source_trail = self.feed_service._source_trail(update)
        source_url = (
            _string(provenance.get("source_url"))
            or _string(metadata.get("source_url"))
            or update.url
            or _first_source_url(source_trail)
        )
        source_fetched_at = (
            _parse_datetime(provenance.get("source_fetched_at"))
            or _parse_datetime(metadata.get("source_fetched_at"))
            or _first_source_trail_datetime(source_trail, "retrieved_at")
        )
        failures = _failure_messages(provenance.get("source_failures")) or _failure_messages(metadata.get("source_failures"))
        if not failures and _string(metadata.get("fetch_error")):
            failures = [_string(metadata.get("fetch_error")) or "Source fetch failed."]

        warnings: list[str] = []
        if not source_url:
            warnings.append("No source URL is attached to this update or its source trail.")
        if not source_trail:
            warnings.append("No source trail is available for this card-producing record.")
        if source_fetched_at and now - _aware(source_fetched_at) > timedelta(hours=stale_after_hours):
            warnings.append(f"Source provenance is older than {stale_after_hours} hours.")

        freshness_status = _dynamic_freshness_status(
            source_url=source_url,
            source_fetched_at=source_fetched_at,
            failures=failures,
            stale_after_hours=stale_after_hours,
            now=now,
        )
        provenance_status = "failed" if failures else "available" if source_trail else "missing"

        return ProvenanceDiagnosticRead(
            update_id=update.id,
            external_id=update.external_id,
            source=update.source,
            headline=update.headline,
            published_at=update.published_at,
            source_url=source_url,
            source_fetched_at=source_fetched_at,
            freshness_status=freshness_status,
            provenance_status=provenance_status,
            source_trail_count=len(source_trail),
            failures=failures,
            warnings=warnings,
        )


def _static_freshness_status(source_available: bool, failures: list[str]) -> str:
    if failures:
        return "failed"
    if not source_available:
        return "missing_source"
    return "fresh"


def _dynamic_freshness_status(
    *,
    source_url: str | None,
    source_fetched_at: datetime | None,
    failures: list[str],
    stale_after_hours: int,
    now: datetime,
) -> str:
    if failures:
        return "failed"
    if not source_url:
        return "missing_source"
    if source_fetched_at and now - _aware(source_fetched_at) > timedelta(hours=stale_after_hours):
        return "stale"
    return "fresh"


def _failure_messages(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if not isinstance(value, list):
        return []
    messages: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            messages.append(item)
        elif isinstance(item, dict):
            message = _string(item.get("message")) or _string(item.get("error"))
            if message:
                messages.append(message)
    return messages


def _first_source_trail_time(metadata: dict[str, Any]) -> str | None:
    source_trail = metadata.get("source_trail")
    if not isinstance(source_trail, list):
        return None
    for item in source_trail:
        if isinstance(item, dict):
            retrieved_at = _datetime_string(item.get("retrieved_at"))
            if retrieved_at:
                return retrieved_at
    return None


def _first_source_trail_datetime(source_trail: list[dict[str, Any]], key: str) -> datetime | None:
    for item in source_trail:
        parsed = _parse_datetime(item.get(key))
        if parsed:
            return parsed
    return None


def _first_source_url(source_trail: list[dict[str, Any]]) -> str | None:
    for item in source_trail:
        url = _string(item.get("url"))
        if url:
            return url
    return None


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _datetime_string(value: Any) -> str | None:
    parsed = _parse_datetime(value)
    return _iso(parsed) if parsed else None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return _aware(value).isoformat() if value else None
