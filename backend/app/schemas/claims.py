"""Schemas for source-backed extracted claims and corrections."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClaimCreate(BaseModel):
    canonical_id: str
    source_system: str | None = None
    source_native_id: str | None = None
    source_url: str | None = None
    policy_item_id: int | None = None
    document_version_id: int | None = None
    subject: str
    predicate: str
    value: str
    claim_type: str | None = None
    value_unit: str | None = None
    value_date: datetime | None = None
    extraction_version: str
    extraction_method: str | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)
    source_page: int | None = Field(default=None, ge=1)
    source_location: str | None = None
    supporting_text: str | None = None
    source_coordinates: dict[str, Any] | None = None
    table_cell: str | None = None
    verified_at: datetime | None = None
    review_state: str = "unreviewed"
    metadata: dict[str, Any] | None = None

    @field_validator("supporting_text")
    @classmethod
    def require_document_for_supporting_text(cls, value: str | None, info):
        if value and not info.data.get("document_version_id"):
            raise ValueError("supporting_text requires document_version_id")
        return value


class ClaimRead(ClaimCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClaimCorrectionCreate(BaseModel):
    correction_reason: str
    corrected_value: str | None = None
    corrected_supporting_text: str | None = None
    review_state: str = "pending"
    verified_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class ClaimRevisionRead(ClaimCorrectionCreate):
    id: int
    claim_id: int
    revision_number: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
