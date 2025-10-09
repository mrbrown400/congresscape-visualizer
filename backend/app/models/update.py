"""Database models for government updates and related metadata."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONBMixin, PrimaryKeyMixin, TimestampMixin


class BranchEnum(str, Enum):
    """Supported branches/sources."""

    HOUSE = "house"
    SENATE = "senate"
    LEGISLATIVE = "legislative"
    JUDICIAL = "judicial"
    EXECUTIVE = "executive"
    AGENCY = "agency"


update_entity_association = Table(
    "update_entities",
    Base.metadata,
    Column("update_id", ForeignKey("government_updates.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
)


class GovernmentUpdate(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Canonical representation of a government action or update."""

    __tablename__ = "government_updates"

    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    branch: Mapped[BranchEnum] = mapped_column(PgEnum(BranchEnum, name="branch_enum"), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    url: Mapped[Optional[str]] = mapped_column(String(500))

    tags: Mapped[List[str]] = mapped_column(ARRAY(String(100)), default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=1536), nullable=True)

    entities: Mapped[List["Entity"]] = relationship(
        back_populates="updates",
        secondary=update_entity_association,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_updates_branch_published", "branch", "published_at"),
        Index(
            "ix_updates_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_ip_ops"},
        ),
    )


class Entity(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Entities (people, agencies, committees) linked to updates."""

    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    updates: Mapped[List[GovernmentUpdate]] = relationship(
        back_populates="entities", secondary=update_entity_association, lazy="selectin"
    )
