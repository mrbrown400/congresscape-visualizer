from __future__ import annotations

import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "metro" / "source_fixtures.json"
REQUIRED_FIELDS = {
    "id",
    "record_type",
    "source_tier",
    "canonical_url",
    "source_url",
    "native_id",
    "retrieval_timestamp",
    "content_type",
    "byte_hash",
    "expected",
    "payload",
}
EXPECTED_IDS = {
    "upcoming-meeting-no-minutes",
    "completed-meeting-final-action",
    "multi-item-agenda",
    "board-report-attachments-history",
    "revised-document-preserves-both",
    "withdrawn-document",
    "committee-member-change",
    "excluded-test-body",
    "api-incomplete-html-fallback",
    "deliberate-source-shape-failure",
    "mirror-replaced-by-official",
}


def load_fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def test_fixture_matrix_has_required_source_shapes_and_provenance() -> None:
    document = load_fixtures()
    fixtures = document["fixtures"]

    assert document["parser_version"]
    assert {fixture["id"] for fixture in fixtures} == EXPECTED_IDS
    assert all(REQUIRED_FIELDS <= fixture.keys() for fixture in fixtures)
    assert all(fixture["byte_hash"].startswith("sha256:") for fixture in fixtures)
    assert all(fixture["expected"].get("state") for fixture in fixtures)


def test_revision_unavailable_fallback_and_allowlist_states_are_preserved() -> None:
    fixtures = {fixture["id"]: fixture for fixture in load_fixtures()["fixtures"]}

    revised = fixtures["revised-document-preserves-both"]["expected"]
    assert revised["revision_numbers"] == [1, 2]
    assert revised["replacement_for"] == "AttachmentId:4401"
    assert fixtures["withdrawn-document"]["expected"]["state"] == "withdrawn"
    assert fixtures["api-incomplete-html-fallback"]["expected"]["fallback_kind"] == "official_html"
    assert fixtures["excluded-test-body"]["expected"]["state"] == "excluded"
    assert fixtures["mirror-replaced-by-official"]["expected"]["freshness_source"] == "official_primary"


def test_fixture_loading_is_deterministic_and_network_free() -> None:
    first = FIXTURE_PATH.read_bytes()
    second = FIXTURE_PATH.read_bytes()
    assert first == second
    assert "httpx" not in FIXTURE_PATH.read_text()
