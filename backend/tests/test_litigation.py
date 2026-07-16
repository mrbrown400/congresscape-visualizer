from __future__ import annotations

import json
from pathlib import Path

from app.ingest.litigation import candidate_is_confirmed, normalize_litigation_case


FIXTURE = Path(__file__).parent / "fixtures" / "litigation" / "people_mover_case.json"


def test_litigation_fixture_preserves_neutral_case_and_document_states() -> None:
    case = normalize_litigation_case(json.loads(FIXTURE.read_text()))

    assert case.confirmed_stakeholder_link is True
    assert [document.claim_class for document in case.documents[:3]] == ["allegation", "procedural_fact", "ruling"]
    assert next(document for document in case.documents if document.access_state == "sealed").content_hash is None
    assert case.documents[-1].revision_of == "doc-complaint"
    assert [event.event_type for event in case.events] == [
        "complaint_filed",
        "motion_filed",
        "order_entered",
        "appeal_filed",
    ]


def test_keyword_only_discovery_candidate_is_not_confirmed() -> None:
    assert candidate_is_confirmed({"title": "People Mover keyword only", "parties": []}) is False
    assert candidate_is_confirmed({"parties": [{"name": "Contractor", "verified_stakeholder": True}]}) is True
