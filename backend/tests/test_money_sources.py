from datetime import datetime, timezone

from app.ingest.money import CBOBillCostEstimateAdapter, money_source_contracts
from app.services.money_context import (
    NO_INFERENCE_NOTE,
    build_bill_money_context,
    build_payload_money_context,
    confidence_label,
)


def test_money_source_contracts_cover_m4_sources() -> None:
    contracts = {contract["source_id"]: contract for contract in money_source_contracts()}

    assert {
        "fec_openfec",
        "lda",
        "usaspending",
        "house_disclosures",
        "senate_disclosures",
        "oge",
        "cbo",
        "appropriations",
    }.issubset(contracts)
    assert contracts["fec_openfec"]["identifiers"]
    assert "topic_context" in contracts["lda"]["supported_relationships"]
    assert contracts["cbo"]["unavailable_state"] == "No CBO cost estimate is published for this bill yet."


def test_cbo_adapter_normalizes_source_backed_fixture() -> None:
    retrieved_at = datetime(2026, 6, 16, tzinfo=timezone.utc)
    records = CBOBillCostEstimateAdapter().normalize(
        {
            "cbo_cost_estimates": [
                {
                    "title": "H.R. 1234 cost estimate",
                    "summary": "CBO estimates implementation would affect direct spending.",
                    "url": "https://www.cbo.gov/publication/12345",
                    "date": "2026-06-15",
                }
            ]
        },
        retrieved_at=retrieved_at,
    )

    assert len(records) == 1
    assert records[0].source_relationship == "direct_source"
    assert records[0].source_links[0].source_system == "cbo"
    assert records[0].source_links[0].url == "https://www.cbo.gov/publication/12345"


def test_cbo_adapter_returns_unavailable_state_without_fixture_records() -> None:
    records = CBOBillCostEstimateAdapter().normalize({"cbo_cost_estimates": []})

    assert records[0].source_relationship == "unavailable"
    assert records[0].status == "unavailable"
    assert records[0].unavailable_reason == "No CBO cost estimate is published for this bill yet."


def test_money_context_assigns_labels_and_source_indexes() -> None:
    source_trail = [
        {
            "label": "FEC filing",
            "source": "fec_openfec",
            "url": "https://api.open.fec.gov/v1/committee/C00000000/",
            "supports": ["money_context"],
            "confidence": "related_entity",
            "source_category": "official",
        }
    ]

    context = build_payload_money_context(
        [
            {
                "label": "Campaign finance filing",
                "value": "Committee filing is available from FEC.",
                "source_relationship": "related_entity",
                "source_system": "fec_openfec",
                "source_url": "https://api.open.fec.gov/v1/committee/C00000000/",
            }
        ],
        source_trail,
        unavailable_note="No money context is available.",
    )

    assert context["money_context_status"] == "available"
    assert context["money_context_note"] == NO_INFERENCE_NOTE
    assert context["money_context"][0]["source_indexes"] == [0]
    assert context["money_context"][0]["confidence_label"] == confidence_label("related_entity")


def test_bill_money_context_uses_cbo_estimate_source() -> None:
    source_trail = [
        {
            "label": "CBO estimate",
            "source": "cbo",
            "url": "https://www.cbo.gov/publication/12345",
            "supports": ["money_context"],
            "confidence": "direct_source",
            "source_category": "official",
        }
    ]

    context = build_bill_money_context(
        bill_metadata={},
        cbo_cost_estimates=[
            {
                "title": "CBO estimate",
                "url": "https://www.cbo.gov/publication/12345",
                "summary": "CBO estimate is published.",
            }
        ],
        source_trail=source_trail,
    )

    assert context["money_context_status"] == "available"
    assert context["money_context"][0]["source_relationship"] == "direct_source"
    assert context["money_context"][0]["source_indexes"] == [0]
