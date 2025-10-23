"""Aggregate daily government activity into a concise briefing."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.update import GovernmentUpdate
from app.schemas.summary import DailyBriefHighlight, DailyBriefResponse
from app.schemas.update import GovernmentUpdateRead
from app.services.personalization import rank_updates


class DailySummaryService:
    """Builds a once-per-day briefing out of individual updates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_brief(self, target_date: date | None = None, *, highlight_limit: int = 3) -> DailyBriefResponse:
        """Return a narrative summary plus spotlight bullets for a given day."""

        window_start, window_end, summary_date = self._time_window(target_date)
        scoped_updates = await self._fetch_updates(window_start, window_end)

        if not scoped_updates:
            scoped_updates = await self._fetch_latest_fallback(limit=highlight_limit)

        ranked = rank_updates(scoped_updates, context={"mode": "daily-summary", "date": summary_date.isoformat()})
        top_updates = ranked[: highlight_limit or 3]

        highlights = [self._to_highlight(update) for update in top_updates]
        narrative = self._compose_narrative(top_updates)

        return DailyBriefResponse(
            summary_date=summary_date,
            generated_at=datetime.now(timezone.utc),
            headline=self._derive_headline(top_updates),
            narrative=narrative,
            highlights=highlights,
            top_updates=[GovernmentUpdateRead.model_validate(update, from_attributes=True) for update in top_updates],
        )

    async def _fetch_updates(self, start: datetime, end: datetime) -> Sequence[GovernmentUpdate]:
        stmt: Select[tuple[GovernmentUpdate]] = (
            select(GovernmentUpdate)
            .where(GovernmentUpdate.published_at >= start, GovernmentUpdate.published_at < end)
            .order_by(GovernmentUpdate.published_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _fetch_latest_fallback(self, *, limit: int) -> Sequence[GovernmentUpdate]:
        stmt: Select[tuple[GovernmentUpdate]] = (
            select(GovernmentUpdate).order_by(GovernmentUpdate.published_at.desc()).limit(max(limit, 3))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def _time_window(self, target_date: date | None) -> tuple[datetime, datetime, date]:
        if target_date is None:
            now = datetime.now(timezone.utc)
            summary_date = now.date()
        else:
            summary_date = target_date
        start = datetime.combine(summary_date, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        return start, end, summary_date

    def _compose_narrative(self, updates: Sequence[GovernmentUpdate]) -> str:
        if not updates:
            return "No notable federal activity recorded today."

        sentences = []
        for update in updates[:3]:
            branch = update.branch.value.replace("_", " ").title()
            headline = update.headline.rstrip(".")
            sentences.append(f"{branch}: {headline}")

        return "Today's key actions — " + "; ".join(sentences) + "."

    def _derive_headline(self, updates: Sequence[GovernmentUpdate]) -> str:
        if not updates:
            return "Nothing major to report today"

        primary = updates[0]
        branch = primary.branch.value.replace("_", " ").title()
        return f"{branch} leads today's briefing"

    def _to_highlight(self, update: GovernmentUpdate) -> DailyBriefHighlight:
        return DailyBriefHighlight(
            headline=update.headline,
            summary=update.summary,
            branch=update.branch.value,
            published_at=update.published_at,
            url=update.url,
            tags=update.tags or [],
        )
