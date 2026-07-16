from __future__ import annotations

from datetime import datetime, timezone

from app.ingest.litigation_registry import build_coverage_report, build_stakeholder_registry, candidate_stakeholders


def test_registry_keeps_aliases_relationships_and_unverified_candidates() -> None:
    registry = build_stakeholder_registry(
        [
            {
                "canonical_id": "la:contractor:1",
                "name": "Verified Contractor",
                "aliases": ["VC Holdings"],
                "relationships": ["project:people-mover", "contract:1"],
                "verification_state": "verified",
            },
            {"canonical_id": "candidate:1", "name": "Unverified Candidate", "verification_state": "unverified"},
        ]
    )

    matches = candidate_stakeholders("VC Holdings and Unverified Candidate", registry)

    assert [match.canonical_id for match in matches] == ["la:contractor:1"]
    assert registry[0].relationships == ("project:people-mover", "contract:1")


def test_coverage_report_exposes_limits_instead_of_claiming_exhaustiveness() -> None:
    report = build_coverage_report(
        courts=["Los Angeles Superior Court", "Central District of California"],
        date_start="2020-01-01",
        date_end="2026-07-14",
        source_completeness={"official": "partial", "courtlistener": "discovery_only"},
        last_successful_retrieval=datetime(2026, 7, 14, tzinfo=timezone.utc),
        blind_spots=["sealed records", "PACER authentication"],
    )

    assert report.source_completeness["official"] == "partial"
    assert report.last_successful_retrieval is not None
    assert report.blind_spots == ("sealed records", "PACER authentication")
