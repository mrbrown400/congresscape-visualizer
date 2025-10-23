"""Pydantic models for notification subscriptions."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PushTokenCreate(BaseModel):
    """Incoming request from the mobile app registering its Expo token."""

    token: str = Field(..., min_length=10)
    platform: str = Field(default="expo")
    timezone: str | None = None


class PushTokenRead(BaseModel):
    """Echo back the stored token with metadata."""

    id: int
    token: str
    platform: str
    timezone: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
