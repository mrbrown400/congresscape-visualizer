"""Runtime ingestion control contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RuntimeRunCreate(BaseModel):
    run_key: str = Field(min_length=1, max_length=255)
    source: str = Field(min_length=1, max_length=120)
    lock_key: str | None = None
    owner: str | None = None
    checkpoint: dict[str, Any] = Field(default_factory=dict)


class RuntimeRunUpdate(BaseModel):
    checkpoint: dict[str, Any] | None = None
    error: str | None = None


class RuntimeRunRead(BaseModel):
    id: int
    run_key: str
    source: str
    status: str
    attempt: int
    started_at: datetime
    finished_at: datetime | None = None
    checkpoint: dict[str, Any] = Field(default_factory=dict)
    replay_of_id: int | None = None
    error: str | None = None


class RuntimeReviewCreate(BaseModel):
    source: str
    reason: str
    run_id: int | None = None
    severity: str = "warning"
    payload: dict[str, Any] = Field(default_factory=dict)
