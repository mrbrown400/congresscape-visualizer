from __future__ import annotations

from app.services.cross_source_matching import candidate_link, exact_identifier_links


def test_exact_identifier_matching_carries_evidence() -> None:
    links = exact_identifier_links(
        {"id": "cfms:CF-26-0308", "council_file_number": "CF-26-0308"},
        {"id": "journal:CF-26-0308", "council_file_number": "CF-26-0308"},
        relation="corroborates",
        evidence="same native council-file number",
    )

    assert links[0].confidence == "exact"
    assert links[0].evidence == ("council_file_number=CF-26-0308", "same native council-file number")


def test_candidate_links_preserve_evidence() -> None:
    link = candidate_link("policy:1", "vendor:1", "context", ["same project name", "manual review required"])

    assert link.left == "policy:1"
    assert link.right == "vendor:1"
    assert link.confidence == "candidate"
    assert link.evidence == ("same project name", "manual review required")
