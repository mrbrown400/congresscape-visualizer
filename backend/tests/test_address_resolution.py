from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.ingest.address_resolution import (
    boundary_matches,
    choose_resolution,
    nearby_entities,
    normalize_address,
    opaque_address_hash,
    parse_address_points,
    parse_census_candidates,
    parse_centerline_candidates,
    point_in_polygon,
)
from app.models.civic import AddressResolution, NearbyEntityMatch


def test_normalization_and_hash_are_unit_safe_without_retaining_raw_address() -> None:
    first = normalize_address("123 Main Street, Apt #4")
    second = normalize_address("123 MAIN ST UNIT 4")
    assert first == second == "123 MAIN ST UNIT 4"
    assert opaque_address_hash(first) == opaque_address_hash(second)
    assert "MAIN" not in opaque_address_hash(first)


def test_exact_match_multiple_match_and_no_match() -> None:
    payload = [
        {"hse_id": "H-1", "pin": "P-1", "latitude": 34.0, "longitude": -118.0, "address": "123 MAIN ST"},
    ]
    exact = parse_address_points(payload, retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert choose_resolution(exact, [], []).status == "resolved"
    assert choose_resolution(exact + exact, [], []).ambiguity_reason == "multiple exact address-point matches"
    assert choose_resolution([], [], []).status == "unavailable"


def test_centerline_interpolation_and_census_fallback_preserve_versions() -> None:
    centerline = parse_centerline_candidates({"candidates": [{"address": "123 MAIN ST", "score": 91, "location": {"x": -118, "y": 34}}]})
    decision = choose_resolution([], centerline, [])
    assert decision.status == "resolved"
    assert decision.candidate is not None
    assert decision.candidate.interpolation_status == "centerline_interpolated"

    census = parse_census_candidates(
        {"result": {"addressMatches": [{"matchedAddress": "123 MAIN ST", "coordinates": {"x": -118, "y": 34}}]}},
        benchmark="Public_AR_Current",
        vintage="Current_Current",
    )
    decision = choose_resolution([], [], census)
    assert decision.candidate is not None
    assert decision.candidate.benchmark == "Public_AR_Current"
    assert decision.candidate.vintage == "Current_Current"
    tied = parse_centerline_candidates(
        {"candidates": [
            {"address": "A", "score": 90, "location": {"x": -118, "y": 34}},
            {"address": "B", "score": 90, "location": {"x": -118, "y": 34}},
        ]}
    )
    assert choose_resolution([], tied, []).status == "ambiguous"


def test_boundary_edge_and_outside_cases_are_explicit() -> None:
    square = [[-118.1, 33.9], [-118.0, 33.9], [-118.0, 34.0], [-118.1, 34.0], [-118.1, 33.9]]
    features = [{"properties": {"district": "13"}, "geometry": {"type": "Polygon", "coordinates": [square]}}]
    assert point_in_polygon((-118.05, 33.95), square)
    assert boundary_matches((-118.1, 33.95), features, boundary_type="city", source_service="fixture", source_layer="13", boundary_version="2021")[0].match_kind == "edge"
    assert boundary_matches((-117.9, 33.95), features, boundary_type="city", source_service="fixture", source_layer="13") == []
    county = [{"properties": {"district": "3", "source_snapshot": "county-2021"}, "geometry": {"type": "Polygon", "coordinates": [square]}}]
    county_match = boundary_matches((-118.05, 33.95), county, boundary_type="county", source_service="fixture", source_layer="26", boundary_version="county-2021")
    assert county_match[0].boundary_version == "county-2021"


def test_nearby_joins_are_versioned_and_keep_route_branches() -> None:
    matches = nearby_entities(
        (-118.0, 34.0),
        [
            {"entity_type": "metro_stop", "source_native_id": "S1", "name": "Main", "latitude": 34.0005, "longitude": -118.0, "source_snapshot": "bus-2026-07", "route_id": "40", "route_branch": "A"},
            {"entity_type": "metro_stop", "source_native_id": "S2", "name": "Old", "latitude": 34.0005, "longitude": -118.0, "source_snapshot": "", "route_id": "40", "route_branch": "B"},
        ],
        radius_meters=100,
    )
    assert [(match.source_native_id, match.route_branch) for match in matches] == [("S1", "A")]
    assert matches[0].metadata["distance_method"] == "haversine"


def test_resolution_tables_create_with_privacy_fields() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        resolution = AddressResolution(
            address_hash="a" * 64,
            lookup_type="address",
            status="resolved",
            retrieved_at=datetime.now(timezone.utc),
            resolved_geographies={"city_council": ["13"]},
        )
        session.add(resolution)
        session.flush()
        session.add(
            NearbyEntityMatch(
                resolution_id=resolution.id,
                entity_type="metro_stop",
                source_native_id="S1",
                name="Main",
                distance_meters=12.5,
                source_snapshot="bus-2026-07",
            )
        )
        session.commit()
        assert session.query(AddressResolution).one().address_hash == "a" * 64
        assert session.query(NearbyEntityMatch).one().source_snapshot == "bus-2026-07"
