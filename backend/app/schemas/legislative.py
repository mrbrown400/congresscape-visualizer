"""Pydantic schemas for canonical legislative records."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


SourceConfidence = Literal["direct_source", "related_entity", "topic_context", "unavailable"]
SourceCategory = Literal["official", "fallback", "supporting", "unavailable"]


class LegislativeSourceLinkBase(BaseModel):
    label: str
    url: HttpUrl
    source_system: str
    retrieved_at: datetime
    published_at: datetime | None = None
    confidence: SourceConfidence = "direct_source"
    source_category: SourceCategory = "official"
    supports: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class LegislativeSourceLinkRead(LegislativeSourceLinkBase):
    id: int

    class Config:
        from_attributes = True
        populate_by_name = True


class CongressionalCommitteeBase(BaseModel):
    committee_code: str
    name: str
    chamber: str | None = None
    committee_type: str | None = None
    parent_committee_code: str | None = None
    jurisdiction: str | None = None
    congress_url: HttpUrl | None = None
    metadata: dict[str, Any] | None = None


class CongressionalCommitteeRead(CongressionalCommitteeBase):
    id: int
    source_links: list[LegislativeSourceLinkRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class BillActionBase(BaseModel):
    canonical_id: str
    action_code: str | None = None
    action_type: str | None = None
    text: str
    acted_at: datetime | None = None
    chamber: str | None = None
    committee_code: str | None = None
    source_url: HttpUrl | None = None
    sequence: int | None = None
    metadata: dict[str, Any] | None = None


class BillActionRead(BillActionBase):
    id: int
    bill_id: int
    source_links: list[LegislativeSourceLinkRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class BillTextVersionBase(BaseModel):
    canonical_id: str
    version_code: str | None = None
    version_name: str | None = None
    published_at: datetime | None = None
    source_url: HttpUrl | None = None
    formats: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class BillTextVersionRead(BillTextVersionBase):
    id: int
    bill_id: int
    source_links: list[LegislativeSourceLinkRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class CongressionalBillBase(BaseModel):
    canonical_id: str
    congress: int
    bill_type: str
    number: str
    origin_chamber: str | None = None
    title: str
    short_title: str | None = None
    introduced_at: datetime | None = None
    latest_action_at: datetime | None = None
    latest_action_text: str | None = None
    policy_area: str | None = None
    congress_url: HttpUrl | None = None
    summaries: list[dict[str, Any]] = Field(default_factory=list)
    cosponsors: list[dict[str, Any]] = Field(default_factory=list)
    amendments: list[dict[str, Any]] = Field(default_factory=list)
    related_bills: list[dict[str, Any]] = Field(default_factory=list)
    subjects: list[dict[str, Any]] = Field(default_factory=list)
    cbo_cost_estimates: list[dict[str, Any]] = Field(default_factory=list)
    crs_reports: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class CongressionalBillRead(CongressionalBillBase):
    id: int
    actions: list[BillActionRead] = Field(default_factory=list)
    text_versions: list[BillTextVersionRead] = Field(default_factory=list)
    committees: list[CongressionalCommitteeRead] = Field(default_factory=list)
    source_links: list[LegislativeSourceLinkRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class CongressionalMemberRead(BaseModel):
    id: int
    bioguide_id: str
    name: str
    party: str | None = None
    state: str | None = None
    district: str | None = None
    chamber: str | None = None
    member_type: str | None = None
    current: bool = True
    congress_url: HttpUrl | None = None
    identifiers: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class CongressionalVoteRead(BaseModel):
    id: int
    canonical_id: str
    chamber: str
    congress: int
    session: str | None = None
    roll_number: str
    vote_date: datetime | None = None
    question: str
    result: str | None = None
    bill_id: int | None = None
    source_url: HttpUrl | None = None
    totals: dict[str, Any] = Field(default_factory=dict)
    party_split: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class CongressionalHearingRead(BaseModel):
    id: int
    canonical_id: str
    event_id: str
    congress: int | None = None
    chamber: str
    committee_id: int | None = None
    title: str
    meeting_type: str | None = None
    status: str | None = None
    scheduled_at: datetime | None = None
    location: str | None = None
    source_url: HttpUrl | None = None
    witnesses: list[dict[str, Any]] = Field(default_factory=list)
    related_bills: list[dict[str, Any]] = Field(default_factory=list)
    videos: list[dict[str, Any]] = Field(default_factory=list)
    transcripts: list[dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DistrictLookupResponse(BaseModel):
    lookup_key: str
    lookup_type: str
    query: str
    state: str | None = None
    district: str | None = None
    source: str
    retrieved_at: datetime
    ambiguity_reason: str | None = None
    representative: CongressionalMemberRead | None = None
    senators: list[CongressionalMemberRead] = Field(default_factory=list)
