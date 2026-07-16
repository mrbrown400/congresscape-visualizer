"""Persistence helpers for the shared civic core."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.civic import (
    AgendaItem,
    FundingEvent,
    Geography,
    GovernmentBody,
    Jurisdiction,
    Meeting,
    Official,
    PolicyAction,
    PolicyItem,
    Project,
    Vote,
)
from app.schemas.civic import (
    AgendaItemCreate,
    FundingEventCreate,
    GeographyCreate,
    GovernmentBodyCreate,
    JurisdictionCreate,
    MeetingCreate,
    OfficialCreate,
    PolicyActionCreate,
    PolicyItemCreate,
    ProjectCreate,
    VoteCreate,
)


class CivicCoreService:
    """Idempotent writer for source-backed shared civic records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_jurisdiction(self, payload: JurisdictionCreate) -> Jurisdiction:
        return await self._upsert(
            Jurisdiction, payload, "name", "kind", "source_authority", "parent_id", "valid_from", "valid_to"
        )

    async def upsert_government_body(self, payload: GovernmentBodyCreate) -> GovernmentBody:
        return await self._upsert(
            GovernmentBody, payload, "jurisdiction_id", "parent_body_id", "name", "body_type", "valid_from", "valid_to"
        )

    async def upsert_official(self, payload: OfficialCreate) -> Official:
        return await self._upsert(
            Official, payload, "government_body_id", "name", "role", "identifiers", "valid_from", "valid_to"
        )

    async def upsert_policy_item(self, payload: PolicyItemCreate) -> PolicyItem:
        return await self._upsert(
            PolicyItem,
            payload,
            "jurisdiction_id",
            "item_type",
            "title",
            "lifecycle_phase",
            "source_status",
            "source_status_code",
            "published_at",
            "valid_from",
            "valid_to",
        )

    async def upsert_policy_action(self, payload: PolicyActionCreate) -> PolicyAction:
        return await self._upsert(
            PolicyAction,
            payload,
            "policy_item_id",
            "actor_body_id",
            "action_type",
            "action_code",
            "event_at",
            "effective_at",
            "sequence",
        )

    async def upsert_meeting(self, payload: MeetingCreate) -> Meeting:
        return await self._upsert(
            Meeting, payload, "government_body_id", "meeting_type", "status", "scheduled_at", "held_at", "location"
        )

    async def upsert_agenda_item(self, payload: AgendaItemCreate) -> AgendaItem:
        return await self._upsert(
            AgendaItem, payload, "meeting_id", "policy_item_id", "ordinal", "title", "requested_action"
        )

    async def upsert_vote(self, payload: VoteCreate) -> Vote:
        return await self._upsert(
            Vote, payload, "policy_item_id", "meeting_id", "question", "result", "voted_at", "totals"
        )

    async def upsert_project(self, payload: ProjectCreate) -> Project:
        return await self._upsert(
            Project, payload, "project_type", "name", "owner_body_id", "status", "starts_at", "ends_at"
        )

    async def upsert_funding_event(self, payload: FundingEventCreate) -> FundingEvent:
        return await self._upsert(
            FundingEvent,
            payload,
            "event_type",
            "amount",
            "currency",
            "unit",
            "fiscal_year",
            "effective_at",
            "payer",
            "payee",
            "policy_item_id",
            "project_id",
        )

    async def upsert_geography(self, payload: GeographyCreate) -> Geography:
        return await self._upsert(
            Geography,
            payload,
            "jurisdiction_id",
            "geography_type",
            "name",
            "geometry_reference",
            "source_snapshot",
            "geometry_hash",
            "effective_from",
            "effective_to",
        )

    async def _upsert(self, model: type, payload: Any, *fields: str):
        record = await self._find(model, payload.canonical_id, payload.source_system, payload.source_native_id)
        values = {
            "canonical_id": payload.canonical_id,
            "source_system": payload.source_system,
            "source_native_id": payload.source_native_id,
            "source_url": str(payload.source_url) if payload.source_url else None,
            "metadata_json": payload.metadata,
            **{field: getattr(payload, field) for field in fields},
        }
        if record is None:
            record = model(**values)
            self.session.add(record)
        else:
            for field, value in values.items():
                setattr(record, field, value)
        await self.session.flush()
        return record

    async def _find(self, model: type, canonical_id: str, source_system: str | None, source_native_id: str | None):
        result = await self.session.execute(select(model).where(model.canonical_id == canonical_id))
        record = result.scalar_one_or_none()
        if record is not None or not source_system or not source_native_id:
            return record
        result = await self.session.execute(
            select(model).where(model.source_system == source_system, model.source_native_id == source_native_id)
        )
        return result.scalar_one_or_none()
