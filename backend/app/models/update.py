"""Database models for government updates and related metadata."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONBMixin, PrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.legislative import (
        BillAction,
        CongressionalBill,
        CongressionalHearing,
        CongressionalVote,
    )


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
    branch: Mapped[BranchEnum] = mapped_column(String(50), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    bill_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("congressional_bills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    bill_action_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bill_actions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("congressional_votes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hearing_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("congressional_hearings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # SQLite compatible tags (stored as JSON)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    # Embedding removed for SQLite
    # embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=1536), nullable=True)

    entities: Mapped[List["Entity"]] = relationship(
        back_populates="updates",
        secondary=update_entity_association,
        lazy="selectin",
    )
    bill: Mapped[Optional["CongressionalBill"]] = relationship(lazy="selectin")
    bill_action: Mapped[Optional["BillAction"]] = relationship(lazy="selectin")
    vote: Mapped[Optional["CongressionalVote"]] = relationship(lazy="selectin")
    hearing: Mapped[Optional["CongressionalHearing"]] = relationship(lazy="selectin")

    # Indexes removed for SQLite
    # __table_args__ = (
    #     Index("ix_updates_branch_published", "branch", "published_at"),
    #     Index(
    #         "ix_updates_embedding",
    #         "embedding",
    #         postgresql_using="ivfflat",
    #         postgresql_ops={"embedding": "vector_ip_ops"},
    #     ),
    # )


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
