"""Declarative base and mixins."""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for SQLAlchemy models."""


class TimestampMixin:
    """Mix-in adding created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PrimaryKeyMixin:
    """Mix-in providing a surrogate primary key."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)


class JSONBMixin:
    """Mix-in providing JSON metadata column helper."""

    @staticmethod
    def jsonb_column(default: Any | None = None, nullable: bool = True):
        from sqlalchemy import JSON

        return mapped_column(JSON, nullable=nullable, default=default)
