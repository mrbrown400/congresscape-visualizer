"""Durable ingestion run, checkpoint, lock, and operator-review records."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin


class IngestionRun(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (UniqueConstraint("run_key", name="uq_ingestion_run_key"),)

    run_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="running")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    replay_of_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="SET NULL"), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceCheckpoint(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_checkpoints"
    __table_args__ = (UniqueConstraint("source", name="uq_source_checkpoint_source"),)

    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cursor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class RuntimeLock(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "runtime_locks"
    __table_args__ = (UniqueConstraint("lock_key", name="uq_runtime_lock_key"),)

    lock_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class ReviewQueueItem(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "runtime_review_queue"
    __table_args__ = (Index("ix_runtime_review_status", "status", "created_at"),)

    run_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False, default="warning")
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
