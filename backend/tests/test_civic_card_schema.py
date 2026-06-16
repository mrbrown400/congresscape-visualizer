from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.civic_card import CivicCard


def _valid_card_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "bill-119-hr-1-introduced",
        "card_type": "bill",
        "branch": "legislative",
        "source": "Congress.gov",
        "headline": "H.R. 1 was introduced",
        "summary": "A bill was introduced in the House.",
        "what_happened": "The bill was introduced and referred to committee.",
        "why_it_matters": "It starts the public lifecycle for the proposal.",
        "published_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        "last_updated_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        "involved": [
            {
                "name": "House Committee on Energy and Commerce",
                "entity_type": "committee",
                "role": "referred committee",
            }
        ],
        "key_claims": [
            {
                "id": "introduced",
                "text": "The bill was introduced in the House.",
                "source_indexes": [0],
            }
        ],
        "money_context_status": "available",
        "money_context": [
            {
                "label": "CBO estimate",
                "value": "Not yet published",
                "source_relationship": "unavailable",
                "unavailable_reason": "CBO has not published a cost estimate.",
            }
        ],
        "source_trail": [
            {
                "label": "Congress.gov bill page",
                "source": "Congress.gov",
                "url": "https://www.congress.gov/bill/119th-congress/house-bill/1",
                "supports": ["introduced"],
            }
        ],
        "tags": ["bill", "introduced"],
    }
    payload.update(overrides)
    return payload


def test_civic_card_accepts_source_backed_claims() -> None:
    card = CivicCard.model_validate(_valid_card_payload())

    assert card.card_type == "bill"
    assert card.source_trail[0].source == "Congress.gov"
    assert card.money_context[0].source_relationship == "unavailable"


def test_civic_card_rejects_unsupported_claims() -> None:
    payload = _valid_card_payload(
        key_claims=[
            {
                "id": "unsupported",
                "text": "A factual claim without source support.",
            }
        ]
    )

    with pytest.raises(ValidationError, match="key_claims.unsupported"):
        CivicCard.model_validate(payload)


def test_civic_card_defines_unavailable_source_state() -> None:
    card = CivicCard.model_validate(
        _valid_card_payload(
            key_claims=[
                {
                    "id": "pending-text",
                    "text": "Official text is not yet available.",
                    "unavailable_reason": "Congress.gov has not published text.",
                }
            ],
            source_trail=[],
            source_trail_status="pending",
            source_trail_note="Congress.gov text endpoint has not published data yet.",
            money_context=[],
            money_context_status="unavailable",
            money_context_note="No official money context is available yet.",
        )
    )

    assert card.source_trail_status == "pending"
    assert card.money_context_status == "unavailable"


def test_civic_card_rejects_available_money_context_without_items() -> None:
    payload = _valid_card_payload(money_context=[], money_context_status="available")

    with pytest.raises(ValidationError, match="money_context_status='available'"):
        CivicCard.model_validate(payload)
