"""API contracts for privacy-aware address and nearby-entity resolution."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AddressResolutionRequest(BaseModel):
    address: str = Field(min_length=3, max_length=500)


class NearbyEntityRead(BaseModel):
    entity_type: str
    source_native_id: str
    name: str
    distance_meters: float
    source_snapshot: str
    route_id: str | None = None
    route_branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddressResolutionRead(BaseModel):
    address_hash: str
    lookup_type: str
    status: str
    source_dataset: str | None = None
    source_service: str | None = None
    source_layer: str | None = None
    source_native_id: str | None = None
    hse_id: str | None = None
    pin: str | None = None
    match_score: float | None = None
    interpolation_status: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    boundary_version: str | None = None
    geometry_hash: str | None = None
    retrieved_at: datetime
    benchmark: str | None = None
    vintage: str | None = None
    distance_method: str
    crs: str
    ambiguity_reason: str | None = None
    resolved_geographies: dict[str, Any] = Field(default_factory=dict)
    nearby_entities: list[NearbyEntityRead] = Field(default_factory=list)
