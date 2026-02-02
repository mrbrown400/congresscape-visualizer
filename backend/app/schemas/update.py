"""Pydantic schemas for API requests/responses."""
from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field, HttpUrl

from app.models.update import BranchEnum


class EntityBase(BaseModel):
    name: str
    type: str
    slug: str


class EntityRead(EntityBase):
    id: int

    class Config:
        from_attributes = True


class GovernmentUpdateBase(BaseModel):
    external_id: str
    source: str
    branch: BranchEnum
    headline: str
    summary: Optional[str]
    full_text: Optional[str]
    published_at: datetime
    event_date: Optional[datetime] = None
    url: Optional[HttpUrl]
    tags: List[str] = []
    metadata: dict | None = Field(default=None, alias="metadata_json")


class GovernmentUpdateCreate(GovernmentUpdateBase):
    embedding: Optional[List[float]] = None
    entity_ids: List[int] = []


class GovernmentUpdateRead(GovernmentUpdateBase):
    id: int
    entities: List[EntityRead] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class FeedQueryParams(BaseModel):
    branch: Optional[BranchEnum] = None
    source: Optional[str] = None
    tag: Optional[str] = None
    search: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 20
    offset: int = 0


class FeedResponse(BaseModel):
    items: List[GovernmentUpdateRead]
    total: int
