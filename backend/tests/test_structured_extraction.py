from __future__ import annotations

import json
from pathlib import Path

from app.services.structured_extraction import SUPPORTED_FIELDS, StructuredFieldExtractor


FIXTURE = Path(__file__).parent / "fixtures" / "metro" / "extraction_record.json"


def test_structured_fields_become_source_backed_claims() -> None:
    result = StructuredFieldExtractor().extract(json.loads(FIXTURE.read_text()))

    assert {claim.claim_type for claim in result.claims} == set(SUPPORTED_FIELDS)
    assert result.claims[0].canonical_id == "la.metro:report:2026-0308:claim:report_identifier"
    assert result.claims[0].source_location["page"] == 4
    assert next(claim for claim in result.claims if claim.claim_type == "amount").value == "1250000.00"


def test_lifecycle_events_are_ordered_by_source_date() -> None:
    result = StructuredFieldExtractor().extract(json.loads(FIXTURE.read_text()))

    assert [event.event_type for event in result.lifecycle] == ["published", "introduced", "final_action"]
    assert result.lifecycle[-1].occurred_at is not None
    assert result.lifecycle[-1].occurred_at.isoformat() == "2026-06-25T15:00:00+00:00"


def test_missing_fields_are_not_invented() -> None:
    result = StructuredFieldExtractor().extract({"canonical_id": "record:1", "fields": {"body": "Board"}})

    assert len(result.claims) == 1
    assert result.claims[0].claim_type == "body"
    assert result.lifecycle == ()
