from __future__ import annotations

import json
from pathlib import Path

from app.ingest.city_clerk import PARSER_VERSION, normalize_council_file


FIXTURE = Path(__file__).parent / "fixtures" / "city_clerk" / "transportation_file.json"


def test_transportation_file_preserves_identity_and_documents() -> None:
    record = normalize_council_file(json.loads(FIXTURE.read_text()))

    assert record.council_file_number == "CF-26-0308"
    assert "cfnumber=CF-26-0308" in record.canonical_url
    assert (record.mover, record.seconder, record.district, record.committee) == (
        "Councilmember A",
        "Councilmember B",
        "13",
        "Transportation Committee",
    )
    assert {document.native_id for document in record.documents} == {"cfms-doc-1", "journal-1", "packet-1"}
    assert all(document.byte_hash.startswith("sha256:") for document in record.documents)
    assert record.parser_version == PARSER_VERSION


def test_lifecycle_events_are_ordered_and_preserve_source_disagreement() -> None:
    record = normalize_council_file(json.loads(FIXTURE.read_text()))

    assert [event.event_type for event in record.events] == [
        "introduced",
        "mayoral_transmission",
        "continued",
        "amended",
        "related",
        "closed",
    ]
    assert record.source_disagreements[0]["field"] == "final_action"
