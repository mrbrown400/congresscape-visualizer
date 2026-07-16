from __future__ import annotations

from app.services.cross_source_matching import RelationshipGraph, candidate_link, exact_identifier_links


def test_exact_identifier_matching_carries_evidence() -> None:
    links = exact_identifier_links(
        {"id": "cfms:CF-26-0308", "council_file_number": "CF-26-0308"},
        {"id": "journal:CF-26-0308", "council_file_number": "CF-26-0308"},
        relation="corroborates",
        evidence="same native council-file number",
    )

    assert links[0].confidence == "exact"
    assert links[0].evidence == ("council_file_number=CF-26-0308", "same native council-file number")


def test_candidate_links_and_merge_split_history_are_queryable() -> None:
    graph = RelationshipGraph()
    graph.add_link(candidate_link("policy:1", "vendor:1", "context", ["same project name", "manual review required"]))
    graph.add_link(candidate_link("vendor:1", "payment:1", "funded_by", ["vendor_id=v1"]))
    graph.record_merge("policy:1", ["vendor:1"], "shared project identifier")
    graph.record_split("vendor:1", ["vendor:1", "vendor:2"], "source-system IDs diverged")

    assert graph.related("policy:1") == ("payment:1", "vendor:1")
    assert [audit.operation for audit in graph.audit] == ["merge", "split"]
    assert graph.links[0].confidence == "candidate"
