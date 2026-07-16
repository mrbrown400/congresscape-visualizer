"""Privacy-aware Los Angeles address and nearby-entity resolution helpers."""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

import httpx

ADDRESS_POINTS_DATASET = "4ca8-mxuh"
CITY_COUNCIL_LAYER = "13"
COUNTY_SUPERVISORIAL_LAYER = "26"
CITY_CENTERLINE_GEOCODER = (
    "https://maps.lacity.org/arcgis/rest/services/Locators/centerlineLocator/GeocodeServer/findAddressCandidates"
)
CENSUS_GEOCODER = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
CITY_COUNCIL_BOUNDARY = "https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/13/query"
COUNTY_SUPERVISORIAL_BOUNDARY = (
    "https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Political_Boundaries/MapServer/26/query"
)


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    source: str
    source_native_id: str | None
    latitude: float | None
    longitude: float | None
    matched_address: str | None = None
    score: float | None = None
    interpolation_status: str = "unknown"
    hse_id: str | None = None
    pin: str | None = None
    benchmark: str | None = None
    vintage: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    status: str
    candidate: ResolutionCandidate | None
    ambiguity_reason: str | None = None
    stages_attempted: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BoundaryMatch:
    boundary_type: str
    district: str | None
    source_service: str
    source_layer: str
    boundary_version: str | None
    geometry_hash: str
    match_kind: str = "contains"


@dataclass(frozen=True, slots=True)
class NearbyEntity:
    entity_type: str
    source_native_id: str
    name: str
    distance_meters: float
    source_snapshot: str
    route_id: str | None = None
    route_branch: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_address(address: str) -> str:
    """Normalize common unit and street variants without retaining the raw input."""

    value = re.sub(r"[.,;]+", " ", address.upper())
    value = re.sub(r"\b(APARTMENT|APT)\s*#?\s*([A-Z0-9-]+)", r" UNIT \2", value)
    value = re.sub(r"\b(SUITE|STE)\s*#?\s*([A-Z0-9-]+)", r" UNIT \2", value)
    replacements = {
        r"\bSTREET\b": "ST",
        r"\bAVENUE\b": "AVE",
        r"\bBOULEVARD\b": "BLVD",
        r"\bROAD\b": "RD",
        r"\bDRIVE\b": "DR",
        r"\bLANE\b": "LN",
        r"\bNORTH\b": "N",
        r"\bSOUTH\b": "S",
        r"\bEAST\b": "E",
        r"\bWEST\b": "W",
    }
    for pattern, replacement in replacements.items():
        value = re.sub(pattern, replacement, value)
    return re.sub(r"\s+", " ", value).strip()


def opaque_address_hash(address: str) -> str:
    """Return the only address-derived identifier safe for persistence and logs."""

    return hashlib.sha256(normalize_address(address).encode("utf-8")).hexdigest()


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    nested_result = payload.get("result")
    if isinstance(nested_result, dict):
        return _records(nested_result)
    for key in ("results", "candidates", "addressMatches", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _coordinates(record: dict[str, Any]) -> tuple[float | None, float | None]:
    location = record.get("location") or record.get("geometry") or {}
    if "x" in location and "y" in location:
        return float(location["y"]), float(location["x"])
    attributes = record.get("attributes") or {}
    latitude = record.get("latitude", record.get("lat", attributes.get("latitude", attributes.get("lat"))))
    longitude = record.get("longitude", record.get("lon", attributes.get("longitude", attributes.get("lon"))))
    if latitude is None or longitude is None:
        return None, None
    return float(latitude), float(longitude)


def parse_address_points(payload: Any, *, retrieved_at: datetime | None = None) -> list[ResolutionCandidate]:
    """Parse Socrata address-point rows, retaining only fields needed for resolution."""

    candidates: list[ResolutionCandidate] = []
    for record in _records(payload):
        attributes = record.get("attributes") or {}
        latitude, longitude = _coordinates(record)
        native_id = record.get("hse_id") or record.get("pin") or attributes.get("hse_id") or attributes.get("pin")
        address = record.get("address") or record.get("full_address") or attributes.get("address")
        candidates.append(
            ResolutionCandidate(
                source="lacity-address-points",
                source_native_id=str(native_id) if native_id else None,
                latitude=latitude,
                longitude=longitude,
                matched_address=address,
                score=float(record.get("score", 100)),
                interpolation_status="exact",
                hse_id=str(record.get("hse_id") or attributes.get("hse_id")) if record.get("hse_id") or attributes.get("hse_id") else None,
                pin=str(record.get("pin") or attributes.get("pin")) if record.get("pin") or attributes.get("pin") else None,
                metadata={
                    "dataset_id": ADDRESS_POINTS_DATASET,
                    "layer": ADDRESS_POINTS_DATASET,
                    "service": f"https://data.lacity.org/resource/{ADDRESS_POINTS_DATASET}.json",
                    "retrieved_at": (retrieved_at or utcnow()).isoformat(),
                },
            )
        )
    return candidates


def parse_centerline_candidates(payload: Any, *, retrieved_at: datetime | None = None) -> list[ResolutionCandidate]:
    """Parse City centerline geocoder candidates; this source is interpolation only."""

    candidates: list[ResolutionCandidate] = []
    for record in _records(payload):
        attributes = record.get("attributes") or {}
        latitude, longitude = _coordinates(record)
        native_id = attributes.get("Ref_ID") or attributes.get("PIN") or record.get("address")
        candidates.append(
            ResolutionCandidate(
                source="lacity-centerline-geocoder",
                source_native_id=str(native_id) if native_id else None,
                latitude=latitude,
                longitude=longitude,
                matched_address=record.get("address") or attributes.get("Match_addr"),
                score=float(record.get("score", attributes.get("Score", 0))) or None,
                interpolation_status="centerline_interpolated",
                metadata={"service": CITY_CENTERLINE_GEOCODER, "retrieved_at": (retrieved_at or utcnow()).isoformat()},
            )
        )
    return candidates


def parse_census_candidates(payload: Any, *, benchmark: str, vintage: str, retrieved_at: datetime | None = None) -> list[ResolutionCandidate]:
    """Parse the explicit Census fallback while preserving benchmark and vintage."""

    candidates: list[ResolutionCandidate] = []
    for record in _records(payload):
        coordinates = record.get("coordinates") or record.get("coordinate") or {}
        latitude = coordinates.get("y", coordinates.get("lat"))
        longitude = coordinates.get("x", coordinates.get("lon"))
        if latitude is None or longitude is None:
            continue
        candidates.append(
            ResolutionCandidate(
                source="census-geocoder",
                source_native_id=record.get("addressComponents", {}).get("zip"),
                latitude=float(latitude),
                longitude=float(longitude),
                matched_address=record.get("matchedAddress") or record.get("address"),
                score=None,
                interpolation_status="census_fallback",
                benchmark=benchmark,
                vintage=vintage,
                metadata={"benchmark": benchmark, "vintage": vintage, "retrieved_at": (retrieved_at or utcnow()).isoformat()},
            )
        )
    return candidates


def choose_resolution(
    exact: Iterable[ResolutionCandidate],
    centerline: Iterable[ResolutionCandidate],
    census: Iterable[ResolutionCandidate],
) -> ResolutionDecision:
    """Choose a source without silently converting ambiguity into a district."""

    exact_candidates = list(exact)
    if len(exact_candidates) == 1:
        return ResolutionDecision("resolved", exact_candidates[0], stages_attempted=("exact",))
    if len(exact_candidates) > 1:
        return ResolutionDecision("ambiguous", None, "multiple exact address-point matches", ("exact",))

    centerline_candidates = sorted(list(centerline), key=lambda item: item.score or 0, reverse=True)
    if centerline_candidates:
        top_score = centerline_candidates[0].score or 0
        tied = [item for item in centerline_candidates if abs((item.score or 0) - top_score) < 1]
        if len(tied) > 1:
            return ResolutionDecision("ambiguous", None, "multiple centerline candidates have the same score", ("exact", "centerline"))
        if top_score >= 75:
            return ResolutionDecision("resolved", centerline_candidates[0], stages_attempted=("exact", "centerline"))

    census_candidates = list(census)
    if len(census_candidates) == 1:
        return ResolutionDecision("resolved", census_candidates[0], stages_attempted=("exact", "centerline", "census"))
    if len(census_candidates) > 1:
        return ResolutionDecision("ambiguous", None, "multiple Census fallback matches", ("exact", "centerline", "census"))
    return ResolutionDecision("unavailable", None, "no address match from configured sources", ("exact", "centerline", "census"))


def _point_on_segment(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> bool:
    px, py = point
    sx, sy = start
    ex, ey = end
    cross = (py - sy) * (ex - sx) - (px - sx) * (ey - sy)
    if abs(cross) > 1e-9:
        return False
    return min(sx, ex) - 1e-9 <= px <= max(sx, ex) + 1e-9 and min(sy, ey) - 1e-9 <= py <= max(sy, ey) + 1e-9


def point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    """Boundary-inclusive ray casting for GeoJSON longitude/latitude rings."""

    inside = False
    x, y = point
    for index, current in enumerate(polygon):
        previous = polygon[index - 1]
        start = (float(previous[0]), float(previous[1]))
        end = (float(current[0]), float(current[1]))
        if _point_on_segment((x, y), start, end):
            return True
        if (start[1] > y) != (end[1] > y) and x < (end[0] - start[0]) * (y - start[1]) / (end[1] - start[1]) + start[0]:
            inside = not inside
    return inside


def geometry_contains(point: tuple[float, float], geometry: dict[str, Any]) -> tuple[bool, bool]:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    polygons = coordinates if kind == "MultiPolygon" else [coordinates]
    for polygon in polygons:
        if not polygon:
            continue
        if point_in_polygon(point, polygon[0]):
            on_edge = any(_point_on_segment(point, tuple(ring[i - 1]), tuple(ring[i])) for ring in polygon for i in range(len(ring)))
            return True, on_edge
    return False, False


def boundary_matches(point: tuple[float, float], features: Iterable[dict[str, Any]], *, boundary_type: str, source_service: str, source_layer: str, boundary_version: str | None = None) -> list[BoundaryMatch]:
    matches: list[BoundaryMatch] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        contains, on_edge = geometry_contains(point, geometry)
        if not contains:
            continue
        properties = feature.get("properties") or {}
        district = properties.get("district") or properties.get("DISTRICT") or properties.get("name") or properties.get("NAME")
        geometry_hash = hashlib.sha256(repr(geometry).encode("utf-8")).hexdigest()
        matches.append(BoundaryMatch(boundary_type, str(district) if district is not None else None, source_service, source_layer, boundary_version, geometry_hash, "edge" if on_edge else "contains"))
    return matches


def haversine_meters(first: tuple[float, float], second: tuple[float, float]) -> float:
    radius = 6_371_000
    lat1, lon1, lat2, lon2 = map(math.radians, (first[1], first[0], second[1], second[0]))
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    value = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return radius * 2 * math.asin(math.sqrt(value))


def nearby_entities(point: tuple[float, float], entities: Iterable[dict[str, Any]], *, radius_meters: float = 1_000) -> list[NearbyEntity]:
    """Join only against versioned snapshot rows; route branches remain separate."""

    matches: list[NearbyEntity] = []
    for entity in entities:
        latitude = entity.get("latitude")
        longitude = entity.get("longitude")
        if latitude is None or longitude is None or not entity.get("source_snapshot"):
            continue
        distance = haversine_meters(point, (float(longitude), float(latitude)))
        if distance > radius_meters:
            continue
        matches.append(
            NearbyEntity(
                entity_type=str(entity.get("entity_type", "unknown")),
                source_native_id=str(entity.get("source_native_id", "")),
                name=str(entity.get("name", "")),
                distance_meters=round(distance, 2),
                source_snapshot=str(entity["source_snapshot"]),
                route_id=entity.get("route_id"),
                route_branch=entity.get("route_branch"),
                metadata={"distance_method": "haversine", "crs": "EPSG:4326", "geometry_hash": entity.get("geometry_hash")},
            )
        )
    return sorted(matches, key=lambda item: (item.distance_meters, item.entity_type, item.source_native_id))


async def fetch_json(client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> Any:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


async def resolve_address_from_sources(address: str, *, client: httpx.AsyncClient | None = None) -> ResolutionDecision:
    """Run exact -> City centerline -> explicit Census fallback in that order."""

    own_client = client is None
    active_client = client or httpx.AsyncClient(timeout=20)
    query = normalize_address(address)
    try:
        exact_payload = await fetch_json(active_client, f"https://data.lacity.org/resource/{ADDRESS_POINTS_DATASET}.json", {"$q": query, "$limit": 10})
        exact = parse_address_points(exact_payload)
        centerline: list[ResolutionCandidate] = []
        census: list[ResolutionCandidate] = []
        if not exact:
            centerline_payload = await fetch_json(active_client, CITY_CENTERLINE_GEOCODER, {"SingleLine": query, "outFields": "*", "f": "json"})
            centerline = parse_centerline_candidates(centerline_payload)
        if not exact and not centerline:
            census_payload = await fetch_json(active_client, CENSUS_GEOCODER, {"address": query, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
            census = parse_census_candidates(census_payload, benchmark="Public_AR_Current", vintage="Current_Current")
        return choose_resolution(exact, centerline, census)
    finally:
        if own_client:
            await active_client.aclose()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
