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
    assert card.source_trail[0].confidence == "direct_source"
    assert card.source_trail[0].source_category == "official"
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


def test_civic_card_accepts_money_context_confidence_labels() -> None:
    card = CivicCard.model_validate(
        _valid_card_payload(
            source_trail=[
                {
                    "label": "CBO cost estimate",
                    "source": "cbo",
                    "url": "https://www.cbo.gov/publication/12345",
                    "supports": ["money_context", "cbo_cost_estimate"],
                    "confidence": "direct_source",
                    "source_category": "official",
                },
                {
                    "label": "LDA filing",
                    "source": "lda",
                    "url": "https://lda.senate.gov/filings/public/filing/example",
                    "supports": ["money_context"],
                    "confidence": "topic_context",
                    "source_category": "supporting",
                },
            ],
            money_context=[
                {
                    "label": "CBO estimate",
                    "value": "Published estimate available.",
                    "source_relationship": "direct_source",
                    "confidence_label": {
                        "relationship": "direct_source",
                        "label": "Direct source match",
                        "description": "The source directly names this bill.",
                    },
                    "source_indexes": [0],
                    "note": "Money context is source-backed context only; it does not imply corruption, motive, or intent.",
                    "source_system": "cbo",
                    "source_category": "official",
                },
                {
                    "label": "Issue lobbying context",
                    "value": "Related quarterly filing.",
                    "source_relationship": "topic_context",
                    "source_indexes": [1],
                    "note": "Shown as topic context, not an accusation.",
                    "source_system": "lda",
                    "source_category": "supporting",
                },
            ],
        )
    )

    assert card.money_context[0].confidence_label["label"] == "Direct source match"
    assert card.money_context[1].source_relationship == "topic_context"
