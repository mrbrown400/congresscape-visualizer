"""Database models for push notification subscriptions."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin


class NotificationSubscription(PrimaryKeyMixin, TimestampMixin, Base):
    """Stores Expo push tokens for devices that opted into alerts."""

    __tablename__ = "notification_subscriptions"

    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="expo")
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    followed_bills: Mapped[list[str]] = mapped_column(JSON, default=list)
    followed_members: Mapped[list[str]] = mapped_column(JSON, default=list)
    followed_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    followed_committees: Mapped[list[str]] = mapped_column(JSON, default=list)
    alert_categories: Mapped[dict] = mapped_column(JSON, default=dict)
    delivery_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SavedFeedFilter(PrimaryKeyMixin, TimestampMixin, Base):
    """A named, device-scoped feed query used by scheduled deliveries."""

    __tablename__ = "saved_feed_filters"
    __table_args__ = (UniqueConstraint("token", "name", name="uq_saved_feed_filter_token_name"),)

    token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)


class NotificationBatch(PrimaryKeyMixin, TimestampMixin, Base):
    """A scheduled delivery window, keyed so reruns are idempotent."""

    __tablename__ = "notification_batches"
    __table_args__ = (UniqueConstraint("batch_key", name="uq_notification_batch_key"),)

    batch_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class NotificationDelivery(PrimaryKeyMixin, TimestampMixin, Base):
    """Per-recipient delivery state with durable duplicate prevention and retries."""

    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_notification_delivery_dedupe_key"),
        Index("ix_notification_delivery_retry", "status", "next_attempt_at"),
    )

    batch_id: Mapped[int] = mapped_column(ForeignKey("notification_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
