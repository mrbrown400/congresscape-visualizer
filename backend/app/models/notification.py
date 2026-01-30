"""Database models for push notification subscriptions."""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin


class NotificationSubscription(PrimaryKeyMixin, TimestampMixin, Base):
    """Stores Expo push tokens for devices that opted into alerts."""

    __tablename__ = "notification_subscriptions"

    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="expo")
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
