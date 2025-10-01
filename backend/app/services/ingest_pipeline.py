"""Utilities to normalize and persist ingestion payloads."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.base import NormalizedUpdate
from app.schemas.update import GovernmentUpdateCreate
from app.services.embedding import EmbeddingService
from app.services.summarization import SummarizationService
from app.services.update_service import UpdateService


class IngestPipeline:
    """Coordinates ingest stages: summarize, embed, persist."""

    def __init__(
        self,
        session: AsyncSession,
        updater: UpdateService,
        summarizer: SummarizationService,
        embedder: EmbeddingService,
    ) -> None:
        self.session = session
        self.updater = updater
        self.summarizer = summarizer
        self.embedder = embedder

    async def handle_updates(self, updates: Iterable[NormalizedUpdate]) -> None:
        for update in updates:
            summary = update.summary or await self.summarizer.summarize(update.full_text)
            embedding = await self.embedder.embed(update.full_text)
            payload = GovernmentUpdateCreate(
                external_id=update.external_id,
                source=update.source,
                branch=update.branch,  # type: ignore[arg-type]
                headline=update.headline,
                summary=summary,
                full_text=update.full_text,
                published_at=update.published_at,
                url=update.url,
                tags=update.tags,
                metadata=update.metadata,
                embedding=embedding,
                entity_ids=[],
            )
            await self.updater.upsert_update(payload)
        await self.session.commit()
