"""Canonical legislative data models for Congress.gov-backed feed records."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONBMixin, PrimaryKeyMixin, TimestampMixin


bill_committee_association = Table(
    "bill_committees",
    Base.metadata,
    Column("bill_id", ForeignKey("congressional_bills.id", ondelete="CASCADE"), primary_key=True),
    Column("committee_id", ForeignKey("congressional_committees.id", ondelete="CASCADE"), primary_key=True),
)


class CongressionalBill(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Canonical bill record keyed by Congress.gov bill identity."""

    __tablename__ = "congressional_bills"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_congressional_bills_canonical_id"),
        Index("ix_congressional_bills_lookup", "congress", "bill_type", "number"),
    )

    canonical_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    congress: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    bill_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    origin_chamber: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    short_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    introduced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_action_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_action_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    congress_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summaries: Mapped[list[dict]] = mapped_column(JSON, default=list)
    cosponsors: Mapped[list[dict]] = mapped_column(JSON, default=list)
    amendments: Mapped[list[dict]] = mapped_column(JSON, default=list)
    related_bills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    subjects: Mapped[list[dict]] = mapped_column(JSON, default=list)
    cbo_cost_estimates: Mapped[list[dict]] = mapped_column(JSON, default=list)
    crs_reports: Mapped[list[dict]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    actions: Mapped[List["BillAction"]] = relationship(
        back_populates="bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    text_versions: Mapped[List["BillTextVersion"]] = relationship(
        back_populates="bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    committees: Mapped[List["CongressionalCommittee"]] = relationship(
        secondary=bill_committee_association,
        back_populates="bills",
        lazy="selectin",
    )
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    votes: Mapped[List["CongressionalVote"]] = relationship(back_populates="bill", lazy="selectin")


class BillAction(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A lifecycle action for a canonical bill."""

    __tablename__ = "bill_actions"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_bill_actions_canonical_id"),
        Index("ix_bill_actions_bill_date", "bill_id", "acted_at"),
    )

    canonical_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("congressional_bills.id", ondelete="CASCADE"), nullable=False)
    action_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    acted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    chamber: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    committee_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    bill: Mapped[CongressionalBill] = relationship(back_populates="actions")
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="action",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BillTextVersion(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Published text version for a bill."""

    __tablename__ = "bill_text_versions"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_bill_text_versions_canonical_id"),
    )

    canonical_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("congressional_bills.id", ondelete="CASCADE"), nullable=False)
    version_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    version_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    formats: Mapped[list[dict]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    bill: Mapped[CongressionalBill] = relationship(back_populates="text_versions")
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="text_version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CongressionalCommittee(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Congressional committee or subcommittee."""

    __tablename__ = "congressional_committees"
    __table_args__ = (
        UniqueConstraint("committee_code", name="uq_congressional_committees_code"),
    )

    committee_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    chamber: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    committee_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    parent_committee_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    congress_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    bills: Mapped[List[CongressionalBill]] = relationship(
        secondary=bill_committee_association,
        back_populates="committees",
        lazy="selectin",
    )
    hearings: Mapped[List["CongressionalHearing"]] = relationship(back_populates="committee", lazy="selectin")
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="committee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CongressionalMember(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Current or historical member record for district and vote matching."""

    __tablename__ = "congressional_members"
    __table_args__ = (
        UniqueConstraint("bioguide_id", name="uq_congressional_members_bioguide"),
        Index("ix_congressional_members_state_district_current", "state", "district", "current"),
    )

    bioguide_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    party: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    district: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    chamber: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    member_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    congress_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    identifiers: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    vote_positions: Mapped[List["MemberVotePosition"]] = relationship(back_populates="member", lazy="selectin")
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CongressionalVote(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Roll-call vote and summary totals."""

    __tablename__ = "congressional_votes"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_congressional_votes_canonical_id"),
        Index("ix_congressional_votes_roll", "chamber", "congress", "session", "roll_number"),
    )

    canonical_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    chamber: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    congress: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    session: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    roll_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    vote_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_bills.id", ondelete="SET NULL"), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    totals: Mapped[dict] = mapped_column(JSON, default=dict)
    party_split: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    bill: Mapped[Optional[CongressionalBill]] = relationship(back_populates="votes", lazy="selectin")
    positions: Mapped[List["MemberVotePosition"]] = relationship(
        back_populates="vote",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="vote",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MemberVotePosition(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """A member's position on a roll-call vote."""

    __tablename__ = "member_vote_positions"
    __table_args__ = (
        UniqueConstraint("vote_id", "member_identifier", name="uq_vote_member_position"),
    )

    vote_id: Mapped[int] = mapped_column(ForeignKey("congressional_votes.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_members.id", ondelete="SET NULL"), nullable=True)
    member_identifier: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    member_name: Mapped[str] = mapped_column(String(255), nullable=False)
    party: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    position: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    vote: Mapped[CongressionalVote] = relationship(back_populates="positions")
    member: Mapped[Optional[CongressionalMember]] = relationship(back_populates="vote_positions", lazy="selectin")


class CongressionalHearing(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Committee meeting or hearing with source-backed availability states."""

    __tablename__ = "congressional_hearings"
    __table_args__ = (
        UniqueConstraint("canonical_id", name="uq_congressional_hearings_canonical_id"),
        Index("ix_congressional_hearings_schedule", "chamber", "scheduled_at"),
    )

    canonical_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    congress: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    chamber: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    committee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_committees.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    meeting_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    witnesses: Mapped[list[dict]] = mapped_column(JSON, default=list)
    related_bills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    videos: Mapped[list[dict]] = mapped_column(JSON, default=list)
    transcripts: Mapped[list[dict]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    committee: Mapped[Optional[CongressionalCommittee]] = relationship(back_populates="hearings", lazy="selectin")
    source_links: Mapped[List["LegislativeSourceLink"]] = relationship(
        back_populates="hearing",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DistrictLookupResult(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Resolved local-government lookup with source and timestamp."""

    __tablename__ = "district_lookup_results"
    __table_args__ = (
        UniqueConstraint("lookup_key", name="uq_district_lookup_results_key"),
    )

    lookup_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    lookup_type: Mapped[str] = mapped_column(String(32), nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    district: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ambiguity_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    representative_member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("congressional_members.id", ondelete="SET NULL"), nullable=True
    )
    senator_member_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    raw_response: Mapped[dict] = mapped_column(JSON, default=dict)

    representative: Mapped[Optional[CongressionalMember]] = relationship(lazy="selectin")


class LegislativeSourceLink(PrimaryKeyMixin, TimestampMixin, JSONBMixin, Base):
    """Official or supporting source link attached to a canonical record."""

    __tablename__ = "legislative_source_links"
    __table_args__ = (
        Index("ix_legislative_source_parent", "bill_id", "vote_id", "hearing_id"),
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence: Mapped[str] = mapped_column(String(80), nullable=False, default="direct_source")
    source_category: Mapped[str] = mapped_column(String(80), nullable=False, default="official")
    supports: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict | None] = JSONBMixin.jsonb_column(default=dict)

    bill_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_bills.id", ondelete="CASCADE"), nullable=True)
    action_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bill_actions.id", ondelete="CASCADE"), nullable=True)
    text_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bill_text_versions.id", ondelete="CASCADE"), nullable=True)
    committee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_committees.id", ondelete="CASCADE"), nullable=True)
    member_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_members.id", ondelete="CASCADE"), nullable=True)
    vote_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_votes.id", ondelete="CASCADE"), nullable=True)
    hearing_id: Mapped[Optional[int]] = mapped_column(ForeignKey("congressional_hearings.id", ondelete="CASCADE"), nullable=True)

    bill: Mapped[Optional[CongressionalBill]] = relationship(back_populates="source_links")
    action: Mapped[Optional[BillAction]] = relationship(back_populates="source_links")
    text_version: Mapped[Optional[BillTextVersion]] = relationship(back_populates="source_links")
    committee: Mapped[Optional[CongressionalCommittee]] = relationship(back_populates="source_links")
    member: Mapped[Optional[CongressionalMember]] = relationship(back_populates="source_links")
    vote: Mapped[Optional[CongressionalVote]] = relationship(back_populates="source_links")
    hearing: Mapped[Optional[CongressionalHearing]] = relationship(back_populates="source_links")
