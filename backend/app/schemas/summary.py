"""Pydantic models describing the daily briefing payload."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

from app.schemas.update import GovernmentUpdateRead


class DailyBriefHighlight(BaseModel):
    """Single bullet that surfaces a notable government action."""

    headline: str
    summary: Optional[str] = None
    branch: str
    published_at: datetime
    event_date: Optional[datetime] = None
    url: Optional[HttpUrl] = None
    tags: List[str] = []


class UpcomingEvent(BaseModel):
    """A future event (effective date, comment deadline, hearing, etc.)."""

    headline: str
    summary: Optional[str] = None
    branch: str
    event_date: datetime
    event_type: str  # "effective_date", "comment_deadline", "hearing", etc.
    url: Optional[HttpUrl] = None
    tags: List[str] = []


class DailyBriefResponse(BaseModel):
    """Top-level response returned to the mobile app."""

    summary_date: date
    generated_at: datetime
    headline: str
    narrative: str
    highlights: List[DailyBriefHighlight]
    top_updates: List[GovernmentUpdateRead]
    upcoming_events: List[UpcomingEvent] = []
