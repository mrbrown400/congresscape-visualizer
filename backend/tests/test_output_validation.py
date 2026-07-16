from app.services.output_validation import (
    sanitize_public_payload,
    validate_accessibility,
    validate_authorization,
    validate_public_item,
    validate_source_support,
    verify_translation,
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


def test_translation_and_accessibility_gates_are_explicit() -> None:
    assert not verify_translation({"locale": "es", "source_text": "Hello"}).valid
    assert verify_translation({"locale": "es", "source_text": "Hello", "translated_text": "Hola", "translation_status": "verified"}).valid
    report = validate_accessibility([{"role": "button"}, {"role": "link", "label": "Open source"}])
    assert [issue.code for issue in report.issues] == ["missing_accessible_label"]


def test_authorization_and_public_minimization_defend_adversarial_payloads() -> None:
    assert not validate_authorization(requested_scope="operator", granted_scopes=set()).valid
    assert validate_authorization(requested_scope="operator", granted_scopes={"operator"}).valid
    payload = {"headline": "Safe", "metadata": {"raw_address": "123 SECRET ST", "source": "official"}, "source_payload": {"token": "x"}}
    assert sanitize_public_payload(payload) == {"headline": "Safe", "metadata": {"source": "official"}}
    sanitized, report = validate_public_item({"source_trail_status": "pending", **payload})
    assert "raw_address" not in str(sanitized)
    assert report.valid
