"""Aggregate daily government activity into a concise briefing."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.update import GovernmentUpdate
from app.schemas.summary import DailyBriefHighlight, DailyBriefResponse, UpcomingEvent
from app.schemas.update import GovernmentUpdateRead
from app.services.personalization import rank_updates


class DailySummaryService:
    """Builds a once-per-day briefing out of individual updates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_brief(self, target_date: date | None = None, *, highlight_limit: int = 3) -> DailyBriefResponse:
        """Return a narrative summary plus spotlight bullets for a given day."""

        window_start, window_end, summary_date = self._time_window(target_date)

        # Fetch today's actual published updates (not future events)
        todays_updates = await self._fetch_todays_updates(window_start, window_end)

        # Fetch upcoming events (future event_dates)
        upcoming = await self._fetch_upcoming_events(summary_date, limit=10)

        # If no today's updates, fall back to recent published updates (excluding future events)
        if not todays_updates:
            todays_updates = await self._fetch_latest_fallback(limit=highlight_limit)

        ranked = rank_updates(todays_updates, context={"mode": "daily-summary", "date": summary_date.isoformat()})

        # Select top updates ensuring branch diversity
        top_updates = self._select_diverse_updates(ranked, limit=highlight_limit or 3)

        highlights = [self._to_highlight(update) for update in top_updates]
        narrative = self._compose_narrative(top_updates)
        upcoming_events = [self._to_upcoming_event(update) for update in upcoming]

        return DailyBriefResponse(
            summary_date=summary_date,
            generated_at=datetime.now(timezone.utc),
            headline=self._derive_headline(top_updates),
            narrative=narrative,
            highlights=highlights,
            top_updates=[GovernmentUpdateRead.model_validate(update, from_attributes=True) for update in ranked[:9]],  # Include more for diversity
            upcoming_events=upcoming_events,
        )

    def _select_diverse_updates(self, updates: Sequence[GovernmentUpdate], limit: int) -> list[GovernmentUpdate]:
        """Select updates ensuring representation from different branches."""
        if len(updates) <= limit:
            return list(updates)

        selected: list[GovernmentUpdate] = []
        seen_branches: set[str] = set()

        # First pass: take one from each branch
        for update in updates:
            branch = self._get_branch_value(update.branch)
            if branch not in seen_branches:
                selected.append(update)
                seen_branches.add(branch)
                if len(selected) >= limit:
                    break

        # Second pass: fill remaining slots with highest ranked
        if len(selected) < limit:
            for update in updates:
                if update not in selected:
                    selected.append(update)
                    if len(selected) >= limit:
                        break

        return selected

    async def _fetch_todays_updates(self, start: datetime, end: datetime) -> Sequence[GovernmentUpdate]:
        """Fetch updates published today (excluding future-dated events)."""
        stmt: Select[tuple[GovernmentUpdate]] = (
            select(GovernmentUpdate)
            .where(
                GovernmentUpdate.published_at >= start,
                GovernmentUpdate.published_at < end,
            )
            .order_by(GovernmentUpdate.published_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _fetch_upcoming_events(self, from_date: date, *, limit: int = 10) -> Sequence[GovernmentUpdate]:
        """Fetch updates with future event_dates."""
        start = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
        # Look ahead 30 days for upcoming events
        end = start + timedelta(days=30)

        stmt: Select[tuple[GovernmentUpdate]] = (
            select(GovernmentUpdate)
            .where(
                GovernmentUpdate.event_date.isnot(None),
                GovernmentUpdate.event_date >= start,
                GovernmentUpdate.event_date < end,
            )
            .order_by(GovernmentUpdate.event_date.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _fetch_latest_fallback(self, *, limit: int) -> Sequence[GovernmentUpdate]:
        """Fetch most recent updates from each branch to ensure diversity."""
        now = datetime.now(timezone.utc)
        all_updates: list[GovernmentUpdate] = []

        # Fetch recent updates from each branch to ensure representation
        for branch in ["executive", "legislative", "judicial"]:
            stmt: Select[tuple[GovernmentUpdate]] = (
                select(GovernmentUpdate)
                .where(
                    GovernmentUpdate.published_at <= now,
                    GovernmentUpdate.branch == branch,
                )
                .order_by(GovernmentUpdate.published_at.desc())
                .limit(3)
            )
            result = await self.session.execute(stmt)
            all_updates.extend(result.scalars().all())

        # Sort by published_at and return top items
        all_updates.sort(key=lambda u: u.published_at, reverse=True)
        return all_updates[:max(limit * 3, 9)]  # Return more items for diversity

    def _time_window(self, target_date: date | None) -> tuple[datetime, datetime, date]:
        if target_date is None:
            now = datetime.now(timezone.utc)
            summary_date = now.date()
        else:
            summary_date = target_date
        start = datetime.combine(summary_date, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        return start, end, summary_date

    def _get_branch_value(self, branch) -> str:
        """Get string value from branch whether it's an enum or already a string."""
        return branch.value if hasattr(branch, "value") else str(branch)

    def _compose_narrative(self, updates: Sequence[GovernmentUpdate]) -> str:
        if not updates:
            return "No notable federal activity recorded today."

        # Build a readable summary showing activity across branches
        branches_active = set()
        for update in updates[:6]:
            branches_active.add(self._get_branch_value(update.branch).title())

        branch_list = sorted(branches_active)
        if len(branch_list) == 1:
            branch_text = branch_list[0]
        elif len(branch_list) == 2:
            branch_text = f"{branch_list[0]} and {branch_list[1]}"
        else:
            branch_text = f"{', '.join(branch_list[:-1])}, and {branch_list[-1]}"

        return f"Today's briefing covers {len(updates)} updates across {branch_text}."

    def _derive_headline(self, updates: Sequence[GovernmentUpdate]) -> str:
        if not updates:
            return "Nothing major to report today"

        primary = updates[0]
        # Use the actual headline from the top update, truncated if needed
        headline = primary.headline
        if len(headline) > 80:
            # Find a good break point
            headline = headline[:77].rsplit(' ', 1)[0] + "..."
        return headline

    def _to_highlight(self, update: GovernmentUpdate) -> DailyBriefHighlight:
        return DailyBriefHighlight(
            headline=update.headline,
            summary=update.summary,
            branch=self._get_branch_value(update.branch),
            published_at=update.published_at,
            event_date=update.event_date,
            url=update.url,
            tags=update.tags or [],
        )

    def _to_upcoming_event(self, update: GovernmentUpdate) -> UpcomingEvent:
        """Convert a GovernmentUpdate with event_date to an UpcomingEvent."""
        event_type = (update.metadata_json or {}).get("event_type", "upcoming")
        return UpcomingEvent(
            headline=update.headline,
            summary=update.summary,
            branch=self._get_branch_value(update.branch),
            event_date=update.event_date,
            event_type=event_type,
            url=update.url,
            tags=update.tags or [],
        )
