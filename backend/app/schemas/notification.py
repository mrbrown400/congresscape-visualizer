"""Pydantic models for notification subscriptions."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AlertCategory = Literal["bill_movement", "representative_vote", "hearing_tomorrow", "new_text", "money_context"]


class AlertCategoryPreferences(BaseModel):
    """User controls for noisy followed-object alert classes."""

    bill_movement: bool = True
    representative_votes: bool = True
    hearing_tomorrow: bool = True
    new_text: bool = True
    money_context: bool = True


class PushTokenCreate(BaseModel):
    """Incoming request from the mobile app registering its Expo token."""

    token: str = Field(..., min_length=10)
    platform: str = Field(default="expo")
    timezone: str | None = None
    followed_bills: list[str] = Field(default_factory=list)
    followed_members: list[str] = Field(default_factory=list)
    followed_topics: list[str] = Field(default_factory=list)
    followed_committees: list[str] = Field(default_factory=list)
    alert_categories: AlertCategoryPreferences = Field(default_factory=AlertCategoryPreferences)


class PushTokenRead(BaseModel):
    """Echo back the stored token with metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    platform: str
    timezone: str | None = None
    followed_bills: list[str] = Field(default_factory=list)
    followed_members: list[str] = Field(default_factory=list)
    followed_topics: list[str] = Field(default_factory=list)
    followed_committees: list[str] = Field(default_factory=list)
    alert_categories: dict = Field(default_factory=dict)
    created_at: datetime


class FollowedAlertRequest(BaseModel):
    """Local followed-object state used to generate source-backed alert payloads."""

    followed_bills: list[str] = Field(default_factory=list)
    followed_members: list[str] = Field(default_factory=list)
    followed_topics: list[str] = Field(default_factory=list)
    followed_committees: list[str] = Field(default_factory=list)
    categories: AlertCategoryPreferences = Field(default_factory=AlertCategoryPreferences)
    limit: int = Field(default=20, ge=1, le=100)
    now: datetime | None = None


class FollowedAlertRead(BaseModel):
    """Source-backed alert candidate ready for push or in-app display."""

    category: AlertCategory
    title: str
    body: str
    update_id: int
    source_url: str
    source_label: str | None = None
    published_at: datetime
    event_date: datetime | None = None
    destination: dict[str, Any]
    match_reasons: list[str] = Field(default_factory=list)


class FollowedAlertResponse(BaseModel):
    """Generated followed-object alerts."""

    items: list[FollowedAlertRead]
    total: int
