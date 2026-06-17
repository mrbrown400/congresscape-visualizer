"""Pydantic schemas for API requests/responses."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.update import BranchEnum


class EntityBase(BaseModel):
    name: str
    type: str
    slug: str


class EntityRead(EntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GovernmentUpdateBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    external_id: str
    source: str
    branch: BranchEnum
    headline: str
    summary: Optional[str]
    full_text: Optional[str]
    published_at: datetime
    event_date: Optional[datetime] = None
    url: Optional[HttpUrl]
    bill_id: Optional[int] = None
    bill_action_id: Optional[int] = None
    vote_id: Optional[int] = None
    hearing_id: Optional[int] = None
    tags: List[str] = []
    metadata: dict | None = Field(default=None, alias="metadata_json")


class GovernmentUpdateCreate(GovernmentUpdateBase):
    embedding: Optional[List[float]] = None
    entity_ids: List[int] = []


class GovernmentUpdateRead(GovernmentUpdateBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    entities: List[EntityRead] = []


class FeedItemRead(GovernmentUpdateRead):
    """Frontend-ready feed item enriched for primary-source civic surfaces."""

    card_type: str
    rank_context: dict[str, Any] = Field(default_factory=dict)
    involved: list[dict[str, Any]] = Field(default_factory=list)
    key_claims: list[dict[str, Any]] = Field(default_factory=list)
    source_trail: list[dict[str, Any]] = Field(default_factory=list)
    source_trail_status: str = "available"
    source_trail_note: str | None = None
    money_context_status: str = "not_applicable"
    money_context_note: str | None = None
    money_context: list[dict[str, Any]] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


class FeedQueryParams(BaseModel):
    branch: Optional[BranchEnum] = None
    source: Optional[str] = None
    tag: Optional[str] = None
    search: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort: Optional[str] = None
    card_type: Optional[str] = None
    followed_bills: Optional[str] = None
    followed_members: Optional[str] = None
    followed_topics: Optional[str] = None
    followed_committees: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    limit: int = 20
    offset: int = 0


class FeedResponse(BaseModel):
    items: List[FeedItemRead]
    total: int
