from app.services.output_validation import (
    sanitize_public_payload,
    validate_public_item,
    validate_source_support,
)


def test_source_support_rejects_unsupported_available_output_but_allows_pending() -> None:
    assert validate_source_support({"source_trail_status": "pending"}).valid
    report = validate_source_support(
        {
            "source_trail_status": "available",
            "source_trail": [],
            "money_context_status": "available",
            "money_context": [{"source_relationship": "unavailable", "source_indexes": []}],
            "summary": "This proves criminal intent.",
        }
    )
    assert {issue.code for issue in report.issues} == {"missing_source_trail", "unsupported_money_context", "non_neutral_copy"}


def test_public_minimization_defends_adversarial_payloads() -> None:
    payload = {"headline": "Safe", "metadata": {"raw_address": "123 SECRET ST", "source": "official"}, "source_payload": {"token": "x"}}
    assert sanitize_public_payload(payload) == {"headline": "Safe", "metadata": {"source": "official"}}
    sanitized, report = validate_public_item({"source_trail_status": "pending", **payload})
    assert "raw_address" not in str(sanitized)
    assert report.valid
