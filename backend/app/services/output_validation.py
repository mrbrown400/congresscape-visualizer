"""Adversarial output checks and public-payload minimization."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_PRIVATE_KEYS = {"raw_address", "address_query", "raw_response", "source_payload", "secret", "access_token"}
_UNSUPPORTED_LANGUAGE = ("corrupt", "bribe", "stole", "criminal intent", "obviously guilty")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(slots=True)
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def add(self, code: str, message: str, severity: str = "error") -> None:
        self.issues.append(ValidationIssue(code, message, severity))


def validate_source_support(item: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    source_trail = item.get("source_trail") or []
    source_status = item.get("source_trail_status")
    if source_status == "available" and not source_trail:
        report.add("missing_source_trail", "Available source state requires at least one source trail entry.")
    for source in source_trail:
        if not isinstance(source, dict) or not source.get("url"):
            report.add("invalid_source_entry", "Every source trail entry must include a URL.")
    if item.get("money_context_status") == "available":
        money = [record for record in item.get("money_context") or [] if isinstance(record, dict)]
        if not money or any(not record.get("source_indexes") or record.get("source_relationship") == "unavailable" for record in money):
            report.add("unsupported_money_context", "Available money context requires supporting source indexes and a non-unavailable relationship.")
    narrative = " ".join(str(item.get(key) or "") for key in ("headline", "summary", "full_text")).lower()
    if any(term in narrative for term in _UNSUPPORTED_LANGUAGE):
        report.add("non_neutral_copy", "Output contains unsupported motive, guilt, or corruption language.")
    return report


def verify_translation(payload: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    locale = str(payload.get("locale") or "en").lower()
    if locale != "en" and payload.get("translation_status") != "verified":
        report.add("unverified_translation", "Non-English output must carry a verified translation status.")
    if locale != "en" and payload.get("source_text") and not payload.get("translated_text"):
        report.add("missing_translation", "A translated output must include translated text.")
    return report


def validate_accessibility(elements: list[dict[str, Any]]) -> ValidationReport:
    report = ValidationReport()
    for index, element in enumerate(elements):
        role = element.get("role")
        if role in {"button", "link", "input", "tab"} and not element.get("label"):
            report.add("missing_accessible_label", f"Interactive element {index} is missing an accessible label.")
    return report


def validate_authorization(*, requested_scope: str, granted_scopes: set[str]) -> ValidationReport:
    report = ValidationReport()
    if requested_scope not in granted_scopes and "admin" not in granted_scopes:
        report.add("forbidden_scope", f"Requested scope '{requested_scope}' is not granted.", severity="error")
    return report


def sanitize_public_payload(value: Any) -> Any:
    """Recursively remove raw/private fields before a payload crosses the API boundary."""

    if isinstance(value, dict):
        return {key: sanitize_public_payload(item) for key, item in value.items() if key not in _PRIVATE_KEYS}
    if isinstance(value, list):
        return [sanitize_public_payload(item) for item in value]
    return value


def validate_public_item(item: dict[str, Any]) -> tuple[dict[str, Any], ValidationReport]:
    report = validate_source_support(item)
    return sanitize_public_payload(item), report
