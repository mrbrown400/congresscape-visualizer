"""Generic civic-core models shared by jurisdiction-specific source packages."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONBMixin, PrimaryKeyMixin, TimestampMixin


class CivicIdentityMixin:
    """Fields common to source-backed canonical records."""

    canonical_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    source_native_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)


policy_item_document_versions = Table(
    "civic_policy_item_document_versions",
    Base.metadata,
    Column("policy_item_id", ForeignKey("civic_policy_items.id", ondelete="CASCADE"), primary_key=True),
    Column("document_version_id", ForeignKey("civic_document_versions.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_civic_policy_item_document_versions_document", "document_version_id"),
)

policy_item_projects = Table(
    "civic_policy_item_projects",
    Base.metadata,
    Column("policy_item_id", ForeignKey("civic_policy_items.id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", ForeignKey("civic_projects.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_civic_policy_item_projects_project", "project_id"),
)

policy_item_geographies = Table(
    "civic_policy_item_geographies",
    Base.metadata,
    Column("policy_item_id", ForeignKey("civic_policy_items.id", ondelete="CASCADE"), primary_key=True),
    Column("geography_id", ForeignKey("civic_geographies.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_civic_policy_item_geographies_geography", "geography_id"),
)

project_geographies = Table(
    "civic_project_geographies",
    Base.metadata,
    Column("project_id", ForeignKey("civic_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("geography_id", ForeignKey("civic_geographies.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_civic_project_geographies_geography", "geography_id"),
)

agenda_item_votes = Table(
    "civic_agenda_item_votes",
    Base.metadata,
    Column("agenda_item_id", ForeignKey("civic_agenda_items.id", ondelete="CASCADE"), primary_key=True),
    Column("vote_id", ForeignKey("civic_votes.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_civic_agenda_item_votes_vote", "vote_id"),
)


class Jurisdiction(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A governing scope and its parent/child relationship."""

    __tablename__ = "civic_jurisdictions"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_jurisdictions_canonical_id"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_authority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_jurisdictions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    parent: Mapped[Optional["Jurisdiction"]] = relationship(
        back_populates="children", remote_side="Jurisdiction.id", foreign_keys=[parent_id]
    )
    children: Mapped[List["Jurisdiction"]] = relationship(back_populates="parent", cascade="all")
    bodies: Mapped[List["GovernmentBody"]] = relationship(back_populates="jurisdiction", cascade="all, delete-orphan")
    policy_items: Mapped[List["PolicyItem"]] = relationship(
        back_populates="jurisdiction", cascade="all, delete-orphan"
    )
    geographies: Mapped[List["Geography"]] = relationship(
        back_populates="jurisdiction", cascade="all, delete-orphan"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="jurisdiction", cascade="all, delete-orphan")


class GovernmentBody(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A body, agency, committee, board, department, or chamber."""

    __tablename__ = "civic_government_bodies"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_government_bodies_canonical_id"),)

    jurisdiction_id: Mapped[int] = mapped_column(
        ForeignKey("civic_jurisdictions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_body_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    body_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    jurisdiction: Mapped[Jurisdiction] = relationship(back_populates="bodies")
    parent_body: Mapped[Optional["GovernmentBody"]] = relationship(
        back_populates="child_bodies", remote_side="GovernmentBody.id", foreign_keys=[parent_body_id]
    )
    child_bodies: Mapped[List["GovernmentBody"]] = relationship(back_populates="parent_body", cascade="all")
    officials: Mapped[List["Official"]] = relationship(back_populates="government_body", passive_deletes=True)
    policy_actions: Mapped[List["PolicyAction"]] = relationship(back_populates="actor_body")
    meetings: Mapped[List["Meeting"]] = relationship(back_populates="government_body", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship(back_populates="owner_body")
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="government_body", cascade="all, delete-orphan")


class Official(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A person or office-holder with a time-bounded role."""

    __tablename__ = "civic_officials"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_officials_canonical_id"),)

    government_body_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    identifiers: Mapped[dict] = mapped_column(JSON, default=dict)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    government_body: Mapped[Optional[GovernmentBody]] = relationship(back_populates="officials")
    vote_positions: Mapped[List["VotePosition"]] = relationship(back_populates="official", passive_deletes=True)
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="official", cascade="all, delete-orphan")


class PolicyItem(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """The durable subject whose lifecycle is followed."""

    __tablename__ = "civic_policy_items"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_civic_policy_items_canonical_id"),
        UniqueConstraint(
            "source_system",
            "source_native_id",
            "item_type",
            name="uq_civic_policy_items_source_identity",
        ),
        Index("ix_civic_policy_items_type_status", "item_type", "lifecycle_phase"),
    )

    jurisdiction_id: Mapped[int] = mapped_column(
        ForeignKey("civic_jurisdictions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    lifecycle_phase: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    source_status: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    source_status_code: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    jurisdiction: Mapped[Jurisdiction] = relationship(back_populates="policy_items")
    actions: Mapped[List["PolicyAction"]] = relationship(
        back_populates="policy_item", cascade="all, delete-orphan", order_by="PolicyAction.sequence"
    )
    agenda_items: Mapped[List["AgendaItem"]] = relationship(back_populates="policy_item")
    votes: Mapped[List["Vote"]] = relationship(back_populates="policy_item")
    document_versions: Mapped[List["DocumentVersion"]] = relationship(
        secondary=policy_item_document_versions, back_populates="policy_items", lazy="selectin"
    )
    projects: Mapped[List["Project"]] = relationship(
        secondary=policy_item_projects, back_populates="policy_items", lazy="selectin"
    )
    funding_events: Mapped[List["FundingEvent"]] = relationship(back_populates="policy_item")
    geographies: Mapped[List["Geography"]] = relationship(
        secondary=policy_item_geographies, back_populates="policy_items", lazy="selectin"
    )
    claims: Mapped[List["ExtractedClaim"]] = relationship(back_populates="policy_item")
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="policy_item", cascade="all, delete-orphan")


class PolicyAction(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """An observed source-native event in a policy item's lifecycle."""

    __tablename__ = "civic_policy_actions"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_civic_policy_actions_canonical_id"),
        Index("ix_civic_policy_actions_item_sequence", "policy_item_id", "sequence"),
    )

    policy_item_id: Mapped[int] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_body_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    action_code: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    event_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    effective_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    policy_item: Mapped[PolicyItem] = relationship(back_populates="actions")
    actor_body: Mapped[Optional[GovernmentBody]] = relationship(back_populates="policy_actions")
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="policy_action", cascade="all, delete-orphan")


class Meeting(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A scheduled or completed public body event."""

    __tablename__ = "civic_meetings"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_meetings_canonical_id"),)

    government_body_id: Mapped[int] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meeting_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    held_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    government_body: Mapped[GovernmentBody] = relationship(back_populates="meetings")
    agenda_items: Mapped[List["AgendaItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", order_by="AgendaItem.ordinal"
    )
    votes: Mapped[List["Vote"]] = relationship(back_populates="meeting")
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class AgendaItem(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A meeting item that may discuss a policy item."""

    __tablename__ = "civic_agenda_items"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_agenda_items_canonical_id"),)

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("civic_meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ordinal: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    requested_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    meeting: Mapped[Meeting] = relationship(back_populates="agenda_items")
    policy_item: Mapped[Optional[PolicyItem]] = relationship(back_populates="agenda_items")
    votes: Mapped[List["Vote"]] = relationship(
        secondary=agenda_item_votes, back_populates="agenda_items", lazy="selectin"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="agenda_item", cascade="all, delete-orphan")


class Vote(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A recorded decision attached to a policy item, meeting, or agenda item."""

    __tablename__ = "civic_votes"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_votes_canonical_id"),)

    policy_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    meeting_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_meetings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    voted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    totals: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    policy_item: Mapped[Optional[PolicyItem]] = relationship(back_populates="votes")
    meeting: Mapped[Optional[Meeting]] = relationship(back_populates="votes")
    agenda_items: Mapped[List[AgendaItem]] = relationship(
        secondary=agenda_item_votes, back_populates="votes", lazy="selectin"
    )
    positions: Mapped[List["VotePosition"]] = relationship(
        back_populates="vote", cascade="all, delete-orphan", lazy="selectin"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="vote", cascade="all, delete-orphan")


class VotePosition(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """An official's recorded position on a vote."""

    __tablename__ = "civic_vote_positions"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_civic_vote_positions_canonical_id"),
        UniqueConstraint("vote_id", "official_id", name="uq_civic_vote_official_position"),
    )

    vote_id: Mapped[int] = mapped_column(ForeignKey("civic_votes.id", ondelete="CASCADE"), nullable=False)
    official_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_officials.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[str] = mapped_column(String(80), nullable=False)
    cast_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    vote: Mapped[Vote] = relationship(back_populates="positions")
    official: Mapped[Optional[Official]] = relationship(back_populates="vote_positions")
    source_links: Mapped[List["SourceLink"]] = relationship(
        back_populates="vote_position", cascade="all, delete-orphan"
    )


class DocumentVersion(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """An immutable retrieved version of a source document or page."""

    __tablename__ = "civic_document_versions"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_civic_document_versions_canonical_id"),
        UniqueConstraint(
            "source_system",
            "source_native_id",
            "revision_key",
            "byte_hash",
            name="uq_civic_document_versions_source_revision",
        ),
    )

    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    byte_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    revision_key: Mapped[str] = mapped_column(String(255), nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(80), nullable=False, default="pending")
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    policy_items: Mapped[List[PolicyItem]] = relationship(
        secondary=policy_item_document_versions, back_populates="document_versions", lazy="selectin"
    )
    claims: Mapped[List["ExtractedClaim"]] = relationship(
        back_populates="document_version", cascade="all, delete-orphan"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(
        back_populates="document_version", cascade="all, delete-orphan"
    )


_IMMUTABLE_DOCUMENT_FIELDS = (
    "canonical_id",
    "source_system",
    "source_native_id",
    "source_url",
    "content_type",
    "published_at",
    "retrieved_at",
    "byte_hash",
    "revision_key",
)

# ponytail: ORM-only immutability keeps SQLite/PostgreSQL behavior aligned; add dialect triggers when
# production migrations need to defend against bulk SQL updates outside the repository.


@event.listens_for(DocumentVersion, "before_update")
def _prevent_document_version_mutation(mapper, connection, target: DocumentVersion) -> None:
    state = inspect(target)
    if any(state.attrs[field].history.has_changes() for field in _IMMUTABLE_DOCUMENT_FIELDS):
        raise ValueError("DocumentVersion identity and retrieved content fields are immutable")


class Project(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A physical or operational effort distinct from a policy decision."""

    __tablename__ = "civic_projects"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_projects_canonical_id"),)

    project_type: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    owner_body_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    owner_body: Mapped[Optional[GovernmentBody]] = relationship(back_populates="projects")
    policy_items: Mapped[List[PolicyItem]] = relationship(
        secondary=policy_item_projects, back_populates="projects", lazy="selectin"
    )
    funding_events: Mapped[List["FundingEvent"]] = relationship(back_populates="project")
    geographies: Mapped[List["Geography"]] = relationship(
        secondary=project_geographies, back_populates="projects", lazy="selectin"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class FundingEvent(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A sourced authorization, budget, obligation, payment, grant, or revenue event."""

    __tablename__ = "civic_funding_events"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_funding_events_canonical_id"),)

    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fiscal_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    effective_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    policy_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    policy_item: Mapped[Optional[PolicyItem]] = relationship(back_populates="funding_events")
    project: Mapped[Optional[Project]] = relationship(back_populates="funding_events")
    source_links: Mapped[List["SourceLink"]] = relationship(
        back_populates="funding_event", cascade="all, delete-orphan"
    )


class Geography(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A versioned place, boundary, route, station, district, or service area."""

    __tablename__ = "civic_geographies"
    __table_args__ = (UniqueConstraint("canonical_id", name="uq_civic_geographies_canonical_id"),)

    jurisdiction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_jurisdictions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    geography_type: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    geometry_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    geometry_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    jurisdiction: Mapped[Optional[Jurisdiction]] = relationship(back_populates="geographies")
    policy_items: Mapped[List[PolicyItem]] = relationship(
        secondary=policy_item_geographies, back_populates="geographies", lazy="selectin"
    )
    projects: Mapped[List[Project]] = relationship(
        secondary=project_geographies, back_populates="geographies", lazy="selectin"
    )
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="geography", cascade="all, delete-orphan")


class ExtractedClaim(CivicIdentityMixin, PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A source-backed assertion extracted from a document or record."""

    __tablename__ = "civic_extracted_claims"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_civic_extracted_claims_canonical_id"),
        Index("ix_civic_claim_document_page", "document_version_id", "source_page"),
        Index("ix_civic_claim_policy_review", "policy_item_id", "review_state"),
        CheckConstraint("source_page IS NULL OR source_page > 0", name="ck_civic_claim_source_page_positive"),
    )

    policy_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_document_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    predicate: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    value_unit: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    value_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extraction_version: Mapped[str] = mapped_column(String(80), nullable=False)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    supporting_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_coordinates: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)
    table_cell: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_state: Mapped[str] = mapped_column(String(80), nullable=False, default="unreviewed")
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    policy_item: Mapped[Optional[PolicyItem]] = relationship(back_populates="claims")
    document_version: Mapped[Optional[DocumentVersion]] = relationship(back_populates="claims")
    source_links: Mapped[List["SourceLink"]] = relationship(back_populates="claim", cascade="all, delete-orphan")


class ClaimRevision(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Correction or verification event for an immutable extracted claim."""

    __tablename__ = "civic_claim_revisions"
    __table_args__ = (
        UniqueConstraint("claim_id", "revision_number", name="uq_civic_claim_revision_number"),
        Index("ix_civic_claim_revisions_claim", "claim_id", "created_at"),
    )

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("civic_extracted_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    correction_reason: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_supporting_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_state: Mapped[str] = mapped_column(String(80), nullable=False, default="pending")
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    claim: Mapped[ExtractedClaim] = relationship(back_populates="revisions")


ExtractedClaim.revisions = relationship(
    ClaimRevision, back_populates="claim", cascade="all, delete-orphan", lazy="selectin"
)


@event.listens_for(ExtractedClaim, "before_update")
def _prevent_claim_fact_mutation(mapper, connection, target: ExtractedClaim) -> None:
    state = inspect(target)
    immutable_fields = (
        "canonical_id",
        "source_system",
        "source_native_id",
        "policy_item_id",
        "document_version_id",
        "subject",
        "predicate",
        "value",
        "supporting_text",
        "source_page",
        "source_location",
    )
    if any(state.attrs[field].history.has_changes() for field in immutable_fields):
        raise ValueError("ExtractedClaim facts are immutable; create a ClaimRevision instead")


class SourceLink(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A provenance citation explicitly attached to one or more civic records."""

    __tablename__ = "civic_source_links"
    __table_args__ = (
        Index("ix_civic_source_link_identity", "source_system", "source_record_kind", "source_native_id"),
        CheckConstraint(
            "document_version_id IS NOT NULL AND "
            "(CASE WHEN jurisdiction_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN government_body_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN official_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN policy_item_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN policy_action_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN meeting_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN agenda_item_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN vote_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN vote_position_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN project_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN funding_event_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN geography_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN claim_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_civic_source_link_has_one_subject_and_document",
        ),
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_record_kind: Mapped[str] = mapped_column(String(120), nullable=False)
    source_native_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[str] = mapped_column(String(80), nullable=False, default="direct_source")
    source_category: Mapped[str] = mapped_column(String(80), nullable=False, default="official")
    support_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    supports: Mapped[list[str]] = mapped_column(JSON, default=list)
    document_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_document_versions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    claim_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_extracted_claims.id", ondelete="CASCADE"), nullable=True, index=True
    )
    jurisdiction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_jurisdictions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    government_body_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_government_bodies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    official_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_officials.id", ondelete="CASCADE"), nullable=True, index=True
    )
    policy_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    policy_action_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_policy_actions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    meeting_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_meetings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    agenda_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_agenda_items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    vote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_votes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    vote_position_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_vote_positions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    funding_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_funding_events.id", ondelete="CASCADE"), nullable=True, index=True
    )
    geography_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("civic_geographies.id", ondelete="CASCADE"), nullable=True, index=True
    )

    document_version: Mapped[Optional[DocumentVersion]] = relationship(back_populates="source_links")
    claim: Mapped[Optional[ExtractedClaim]] = relationship(back_populates="source_links")
    jurisdiction: Mapped[Optional[Jurisdiction]] = relationship(back_populates="source_links")
    government_body: Mapped[Optional[GovernmentBody]] = relationship(back_populates="source_links")
    official: Mapped[Optional[Official]] = relationship(back_populates="source_links")
    policy_item: Mapped[Optional[PolicyItem]] = relationship(back_populates="source_links")
    policy_action: Mapped[Optional[PolicyAction]] = relationship(back_populates="source_links")
    meeting: Mapped[Optional[Meeting]] = relationship(back_populates="source_links")
    agenda_item: Mapped[Optional[AgendaItem]] = relationship(back_populates="source_links")
    vote: Mapped[Optional[Vote]] = relationship(back_populates="source_links")
    vote_position: Mapped[Optional[VotePosition]] = relationship(back_populates="source_links")
    project: Mapped[Optional[Project]] = relationship(back_populates="source_links")
    funding_event: Mapped[Optional[FundingEvent]] = relationship(back_populates="source_links")
    geography: Mapped[Optional[Geography]] = relationship(back_populates="source_links")


__all__ = [
    "AgendaItem",
    "DocumentVersion",
    "ExtractedClaim",
    "FundingEvent",
    "Geography",
    "GovernmentBody",
    "Jurisdiction",
    "Meeting",
    "Official",
    "PolicyAction",
    "PolicyItem",
    "Project",
    "SourceLink",
    "Vote",
    "VotePosition",
]
