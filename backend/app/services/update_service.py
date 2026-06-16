"""Persistence helpers for government updates."""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.update import Entity, GovernmentUpdate
from app.schemas.update import GovernmentUpdateCreate


class UpdateService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _resolve_entities(self, entity_ids: Iterable[int]) -> list[Entity]:
        if not entity_ids:
            return []
        stmt = select(Entity).where(Entity.id.in_(entity_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_update(self, payload: GovernmentUpdateCreate) -> GovernmentUpdate:
        entities = await self._resolve_entities(payload.entity_ids)
        update = GovernmentUpdate(
            external_id=payload.external_id,
            source=payload.source,
            branch=payload.branch,
            headline=payload.headline,
            summary=payload.summary,
            full_text=payload.full_text,
            published_at=payload.published_at,
            event_date=payload.event_date,
            url=str(payload.url) if payload.url else None,
            bill_id=payload.bill_id,
            bill_action_id=payload.bill_action_id,
            vote_id=payload.vote_id,
            hearing_id=payload.hearing_id,
            tags=payload.tags,
            metadata_json=payload.metadata or {},
            # embedding=payload.embedding, # Removed for SQLite
            entities=entities,
        )
        self.session.add(update)
        await self.session.flush()
        return update

    async def upsert_update(self, payload: GovernmentUpdateCreate) -> GovernmentUpdate:
        stmt = select(GovernmentUpdate).where(
            GovernmentUpdate.external_id == payload.external_id,
            GovernmentUpdate.source == payload.source,
        )
        result = await self.session.execute(stmt)
        existing: Optional[GovernmentUpdate] = result.scalar_one_or_none()

        if existing:
            existing.headline = payload.headline
            existing.summary = payload.summary
            existing.full_text = payload.full_text
            existing.published_at = payload.published_at
            existing.event_date = payload.event_date
            existing.url = str(payload.url) if payload.url else None
            existing.bill_id = payload.bill_id
            existing.bill_action_id = payload.bill_action_id
            existing.vote_id = payload.vote_id
            existing.hearing_id = payload.hearing_id
            existing.tags = payload.tags
            existing.metadata_json = payload.metadata or {}
            # existing.embedding = payload.embedding # Removed for SQLite
            existing.entities = await self._resolve_entities(payload.entity_ids)
            await self.session.flush()
            return existing

        return await self.create_update(payload)
