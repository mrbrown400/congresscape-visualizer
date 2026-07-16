"""Schemas for the additive shared civic core."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CivicIdentityRequest(BaseModel):
    canonical_id: str
    source_system: str | None = None
    source_native_id: str | None = None
    source_url: HttpUrl | None = None
    metadata: dict[str, Any] | None = Field(default=None, alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class CivicIdentityRead(CivicIdentityRequest):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class JurisdictionCreate(CivicIdentityRequest):
    name: str
    kind: str
    source_authority: str | None = None
    parent_id: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class JurisdictionRead(JurisdictionCreate, CivicIdentityRead):
    pass


class GovernmentBodyCreate(CivicIdentityRequest):
    jurisdiction_id: int
    parent_body_id: int | None = None
    name: str
    body_type: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class GovernmentBodyRead(GovernmentBodyCreate, CivicIdentityRead):
    pass


class OfficialCreate(CivicIdentityRequest):
    government_body_id: int | None = None
    name: str
    role: str | None = None
    identifiers: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class OfficialRead(OfficialCreate, CivicIdentityRead):
    pass


class PolicyItemCreate(CivicIdentityRequest):
    jurisdiction_id: int
    item_type: str
    title: str
    lifecycle_phase: str | None = None
    source_status: str | None = None
    source_status_code: str | None = None
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class PolicyItemRead(PolicyItemCreate, CivicIdentityRead):
    pass


class PolicyActionCreate(CivicIdentityRequest):
    policy_item_id: int
    actor_body_id: int | None = None
    action_type: str
    action_code: str | None = None
    event_at: datetime | None = None
    effective_at: datetime | None = None
    sequence: int | None = None


class PolicyActionRead(PolicyActionCreate, CivicIdentityRead):
    pass


class MeetingCreate(CivicIdentityRequest):
    government_body_id: int
    meeting_type: str
    status: str | None = None
    scheduled_at: datetime | None = None
    held_at: datetime | None = None
    location: str | None = None


class MeetingRead(MeetingCreate, CivicIdentityRead):
    pass


class AgendaItemCreate(CivicIdentityRequest):
    meeting_id: int
    policy_item_id: int | None = None
    ordinal: int | None = None
    title: str
    requested_action: str | None = None


class AgendaItemRead(AgendaItemCreate, CivicIdentityRead):
    pass


class VoteCreate(CivicIdentityRequest):
    policy_item_id: int | None = None
    meeting_id: int | None = None
    question: str
    result: str | None = None
    voted_at: datetime | None = None
    totals: dict[str, Any] = Field(default_factory=dict)


class VoteRead(VoteCreate, CivicIdentityRead):
    pass


class ProjectCreate(CivicIdentityRequest):
    project_type: str
    name: str
    owner_body_id: int | None = None
    status: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ProjectRead(ProjectCreate, CivicIdentityRead):
    pass


class FundingEventCreate(CivicIdentityRequest):
    event_type: str
    amount: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    fiscal_year: int | None = None
    effective_at: datetime | None = None
    payer: str | None = None
    payee: str | None = None
    policy_item_id: int | None = None
    project_id: int | None = None


class FundingEventRead(FundingEventCreate, CivicIdentityRead):
    pass


class GeographyCreate(CivicIdentityRequest):
    jurisdiction_id: int | None = None
    geography_type: str
    name: str
    geometry_reference: str | None = None
    source_snapshot: str | None = None
    geometry_hash: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class GeographyRead(GeographyCreate, CivicIdentityRead):
    pass
