"""Address, boundary, nearby-entity, and privacy-reset endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.ingest.address_resolution import (
    boundary_matches,
    nearby_entities,
    opaque_address_hash,
    resolve_address_from_sources,
)
from app.models.civic import AddressResolution, Geography, NearbyEntityMatch
from app.schemas.address_resolution import AddressResolutionRead, AddressResolutionRequest, NearbyEntityRead

router = APIRouter()
_NEARBY_TYPES = ("metro_route", "metro_stop", "metro_station", "metro_project")
_BOUNDARY_TYPES = ("city_council_district", "county_supervisorial_district")


def _snapshot_version(features: list[dict]) -> str | None:
    versions = {feature.get("boundary_version") or feature.get("source_snapshot") for feature in features}
    versions.discard(None)
    return next(iter(versions)) if len(versions) == 1 else None


def _read_nearby(match: NearbyEntityMatch) -> NearbyEntityRead:
    return NearbyEntityRead(
        entity_type=match.entity_type,
        source_native_id=match.source_native_id,
        name=match.name,
        distance_meters=float(match.distance_meters),
        source_snapshot=match.source_snapshot,
        route_id=match.route_id,
        route_branch=match.route_branch,
        metadata={
            "source_dataset": match.source_dataset,
            "source_service": match.source_service,
            "source_layer": match.source_layer,
            "boundary_version": match.boundary_version,
            "distance_method": match.distance_method,
            "crs": match.crs,
            "geometry_hash": match.geometry_hash,
        },
    )


async def _read_resolution(session: AsyncSession, resolution: AddressResolution) -> AddressResolutionRead:
    result = await session.execute(
        select(NearbyEntityMatch).where(NearbyEntityMatch.resolution_id == resolution.id).order_by(NearbyEntityMatch.distance_meters)
    )
    return AddressResolutionRead(
        address_hash=resolution.address_hash,
        lookup_type=resolution.lookup_type,
        status=resolution.status,
        source_dataset=resolution.source_dataset,
        source_service=resolution.source_service,
        source_layer=resolution.source_layer,
        source_native_id=resolution.source_native_id,
        hse_id=resolution.hse_id,
        pin=resolution.pin,
        match_score=float(resolution.match_score) if resolution.match_score is not None else None,
        interpolation_status=resolution.interpolation_status,
        latitude=float(resolution.latitude) if resolution.latitude is not None else None,
        longitude=float(resolution.longitude) if resolution.longitude is not None else None,
        boundary_version=resolution.boundary_version,
        geometry_hash=resolution.geometry_hash,
        retrieved_at=resolution.retrieved_at,
        benchmark=resolution.benchmark,
        vintage=resolution.vintage,
        distance_method=resolution.distance_method,
        crs=resolution.crs,
        ambiguity_reason=resolution.ambiguity_reason,
        resolved_geographies=resolution.resolved_geographies or {},
        nearby_entities=[_read_nearby(match) for match in result.scalars().all()],
    )


@router.post("/resolve", response_model=AddressResolutionRead, status_code=status.HTTP_200_OK)
async def resolve_address(
    request: AddressResolutionRequest,
    session: AsyncSession = Depends(get_db),
) -> AddressResolutionRead:
    """Resolve an address without persisting the raw address or a ZIP-derived district."""

    address_hash = opaque_address_hash(request.address)
    existing = await session.scalar(select(AddressResolution).where(AddressResolution.address_hash == address_hash))
    if existing is not None:
        return await _read_resolution(session, existing)

    decision = await resolve_address_from_sources(request.address)
    candidate = decision.candidate
    resolution = AddressResolution(
        address_hash=address_hash,
        lookup_type="address",
        status=decision.status,
        source_dataset=(candidate.metadata.get("dataset_id") if candidate else None),
        source_service=(candidate.metadata.get("service") if candidate else None),
        source_layer=(candidate.metadata.get("layer") if candidate else None),
        source_native_id=candidate.source_native_id if candidate else None,
        hse_id=candidate.hse_id if candidate else None,
        pin=candidate.pin if candidate else None,
        match_score=Decimal(str(candidate.score)) if candidate and candidate.score is not None else None,
        interpolation_status=candidate.interpolation_status if candidate else None,
        latitude=Decimal(str(candidate.latitude)) if candidate and candidate.latitude is not None else None,
        longitude=Decimal(str(candidate.longitude)) if candidate and candidate.longitude is not None else None,
        retrieved_at=datetime.now(timezone.utc),
        benchmark=candidate.benchmark if candidate else None,
        vintage=candidate.vintage if candidate else None,
        ambiguity_reason=decision.ambiguity_reason,
        resolved_geographies={},
    )
    if candidate:
        boundary_result = await session.execute(select(Geography).where(Geography.geography_type.in_(_BOUNDARY_TYPES)))
        boundary_rows = list(boundary_result.scalars().all())
        point = (candidate.longitude, candidate.latitude)
        city_features = [row.metadata_json for row in boundary_rows if row.geography_type == "city_council_district" and row.metadata_json]
        county_features = [row.metadata_json for row in boundary_rows if row.geography_type == "county_supervisorial_district" and row.metadata_json]
        city_matches = boundary_matches(point, city_features, boundary_type="city_council_district", source_service="stored-boundary-snapshot", source_layer="13", boundary_version=_snapshot_version(city_features))
        county_matches = boundary_matches(point, county_features, boundary_type="county_supervisorial_district", source_service="stored-boundary-snapshot", source_layer="26", boundary_version=_snapshot_version(county_features))
        resolution.resolved_geographies = {
            "city_council": [match.district for match in city_matches],
            "county_supervisorial": [match.district for match in county_matches],
            "boundary_status": "ambiguous" if len(city_matches) > 1 or len(county_matches) > 1 else "resolved" if city_matches or county_matches else "unavailable",
            "boundary_versions": sorted({match.boundary_version for match in city_matches + county_matches if match.boundary_version}),
            "geometry_hashes": sorted({match.geometry_hash for match in city_matches + county_matches}),
            "boundary_sources": [
                {
                    "service": match.source_service,
                    "layer": match.source_layer,
                    "version": match.boundary_version,
                    "geometry_hash": match.geometry_hash,
                }
                for match in city_matches + county_matches
            ],
        }
        if len(city_matches) > 1 or len(county_matches) > 1:
            resolution.status = "ambiguous"
            resolution.ambiguity_reason = "point falls in multiple versioned boundary features"
        if city_matches + county_matches:
            resolution.boundary_version = (city_matches + county_matches)[0].boundary_version
            resolution.geometry_hash = (city_matches + county_matches)[0].geometry_hash
            resolution.source_layer = ",".join(sorted({match.source_layer for match in city_matches + county_matches}))

        nearby_result = await session.execute(select(Geography).where(Geography.geography_type.in_(_NEARBY_TYPES)))
        nearby_rows = list(nearby_result.scalars().all())
        entities = []
        for row in nearby_rows:
            metadata = row.metadata_json or {}
            entities.append({
                "entity_type": row.geography_type,
                "source_native_id": row.source_native_id or row.canonical_id,
                "name": row.name,
                "latitude": metadata.get("latitude"),
                "longitude": metadata.get("longitude"),
                "source_snapshot": row.source_snapshot,
                "route_id": metadata.get("route_id"),
                "route_branch": metadata.get("route_branch"),
                "geometry_hash": row.geometry_hash,
            })
        for match in nearby_entities(point, entities):
            session.add(NearbyEntityMatch(
                resolution=resolution,
                entity_type=match.entity_type,
                source_native_id=match.source_native_id,
                name=match.name,
                distance_meters=Decimal(str(match.distance_meters)),
                source_snapshot=match.source_snapshot,
                route_id=match.route_id,
                route_branch=match.route_branch,
                geometry_hash=match.metadata.get("geometry_hash"),
            ))
    session.add(resolution)
    await session.commit()
    await session.refresh(resolution)
    return await _read_resolution(session, resolution)


@router.delete("/resolve/{address_hash}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_address_resolution(address_hash: str, session: AsyncSession = Depends(get_db)) -> Response:
    """Delete a resolution by opaque hash so a user can clear or correct it."""

    if len(address_hash) != 64 or any(char not in "0123456789abcdef" for char in address_hash.lower()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="address_hash must be a SHA-256 hex digest")
    result = await session.execute(delete(AddressResolution).where(AddressResolution.address_hash == address_hash.lower()))
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="address resolution not found")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
