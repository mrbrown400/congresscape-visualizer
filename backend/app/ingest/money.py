"""Money and disclosure source adapter boundaries.

The adapters in this module intentionally define source contracts and fixture
normalization without making live network calls. Concrete fetchers can be added
behind these boundaries once credentials, rate limits, and source-specific
freshness policies are ready.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

MoneySourceStatus = Literal["available", "pending", "unavailable", "error"]
MoneySourceRelationship = Literal["direct_source", "related_entity", "topic_context", "unavailable"]


@dataclass(frozen=True, slots=True)
class MoneySourceDefinition:
    """Static contract for an official money or disclosure source."""

    source_id: str
    label: str
    base_url: str
    identifiers: tuple[str, ...]
    source_category: Literal["official", "supporting", "fallback"] = "official"
    freshness_expectation: str = "Refresh when source payload is retrieved."
    unavailable_state: str = "Source data is not available for this card yet."
    supported_relationships: tuple[MoneySourceRelationship, ...] = ("direct_source",)


@dataclass(frozen=True, slots=True)
class MoneyContextSourceLink:
    """Source link attached to a money-context claim."""

    label: str
    url: str
    source_system: str
    retrieved_at: datetime
    published_at: datetime | None = None
    supports: tuple[str, ...] = ("money_context",)
    confidence: MoneySourceRelationship = "direct_source"
    source_category: str = "official"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_source_link_payload(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "url": self.url,
            "source_system": self.source_system,
            "retrieved_at": self.retrieved_at,
            "published_at": self.published_at,
            "supports": list(self.supports),
            "confidence": self.confidence,
            "source_category": self.source_category,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class MoneyContextRecord:
    """Normalized money context emitted by a source adapter."""

    label: str
    source_relationship: MoneySourceRelationship
    status: MoneySourceStatus = "available"
    value: str | None = None
    note: str | None = None
    unavailable_reason: str | None = None
    source_links: tuple[MoneyContextSourceLink, ...] = ()
    source_system: str | None = None
    source_category: str = "official"
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_money_context_payload(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "source_relationship": self.source_relationship,
            "status": self.status,
            "note": self.note,
            "unavailable_reason": self.unavailable_reason,
            "source_system": self.source_system,
            "source_category": self.source_category,
            "source_urls": [source.url for source in self.source_links],
            "metadata": self.metadata,
        }


class MoneySourceAdapter(Protocol):
    """Protocol for source-specific money context adapters."""

    source: MoneySourceDefinition

    def normalize(self, payload: dict[str, Any], *, retrieved_at: datetime | None = None) -> list[MoneyContextRecord]:
        ...


MONEY_SOURCE_DEFINITIONS: dict[str, MoneySourceDefinition] = {
    "fec_openfec": MoneySourceDefinition(
        source_id="fec_openfec",
        label="FEC/OpenFEC",
        base_url="https://api.open.fec.gov/developers/",
        identifiers=("candidate_id", "committee_id", "cycle", "donor_name", "organization_name"),
        freshness_expectation="Refresh per FEC filing cycle or when candidate/committee context changes.",
        unavailable_state="No FEC/OpenFEC campaign finance context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "topic_context", "unavailable"),
    ),
    "lda": MoneySourceDefinition(
        source_id="lda",
        label="Lobbying Disclosure Act",
        base_url="https://lda.senate.gov/system/public/",
        identifiers=("registrant_id", "client_name", "lobbyist_name", "issue_code", "filing_period"),
        freshness_expectation="Refresh when quarterly LDA filings are retrieved.",
        unavailable_state="No LDA lobbying disclosure context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "topic_context", "unavailable"),
    ),
    "usaspending": MoneySourceDefinition(
        source_id="usaspending",
        label="USAspending.gov",
        base_url="https://api.usaspending.gov/",
        identifiers=("recipient_uei", "recipient_name", "award_id", "agency_code", "naics"),
        freshness_expectation="Refresh when USAspending award data is retrieved for a named organization.",
        unavailable_state="No USAspending award context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "topic_context", "unavailable"),
    ),
    "house_disclosures": MoneySourceDefinition(
        source_id="house_disclosures",
        label="House financial disclosures",
        base_url="https://disclosures-clerk.house.gov/",
        identifiers=("bioguide_id", "member_name", "filing_year", "document_id"),
        freshness_expectation="Refresh when official House disclosure records are retrieved.",
        unavailable_state="No House disclosure context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "unavailable"),
    ),
    "senate_disclosures": MoneySourceDefinition(
        source_id="senate_disclosures",
        label="Senate financial disclosures",
        base_url="https://efdsearch.senate.gov/",
        identifiers=("bioguide_id", "member_name", "filing_year", "document_id"),
        freshness_expectation="Refresh when official Senate disclosure records are retrieved.",
        unavailable_state="No Senate disclosure context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "unavailable"),
    ),
    "oge": MoneySourceDefinition(
        source_id="oge",
        label="Office of Government Ethics",
        base_url="https://www.oge.gov/",
        identifiers=("official_name", "agency", "filing_year", "document_id"),
        freshness_expectation="Refresh when official OGE disclosure records are retrieved.",
        unavailable_state="No OGE disclosure context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "unavailable"),
    ),
    "cbo": MoneySourceDefinition(
        source_id="cbo",
        label="Congressional Budget Office",
        base_url="https://www.cbo.gov/",
        identifiers=("congress", "bill_type", "bill_number", "estimate_id", "url"),
        freshness_expectation="Refresh when Congress.gov or CBO publishes a cost estimate link.",
        unavailable_state="No CBO cost estimate is published for this bill yet.",
        supported_relationships=("direct_source", "unavailable"),
    ),
    "appropriations": MoneySourceDefinition(
        source_id="appropriations",
        label="Appropriations links",
        base_url="https://www.congress.gov/",
        identifiers=("bill_canonical_id", "appropriation_account", "committee_code", "fiscal_year"),
        freshness_expectation="Refresh when official appropriations bill actions or reports are retrieved.",
        unavailable_state="No sourced appropriations context is attached for this card.",
        supported_relationships=("direct_source", "related_entity", "topic_context", "unavailable"),
    ),
}


class CBOBillCostEstimateAdapter:
    """Thin adapter for CBO estimate records already exposed by Congress.gov."""

    source = MONEY_SOURCE_DEFINITIONS["cbo"]

    def normalize(self, payload: dict[str, Any], *, retrieved_at: datetime | None = None) -> list[MoneyContextRecord]:
        retrieved = retrieved_at or datetime.now(timezone.utc)
        estimates = _as_list(payload.get("cbo_cost_estimates") or payload.get("cboCostEstimates"))
        if not estimates:
            return [
                MoneyContextRecord(
                    label="CBO cost estimate",
                    source_relationship="unavailable",
                    status="unavailable",
                    unavailable_reason=self.source.unavailable_state,
                    source_system=self.source.source_id,
                    source_category="unavailable",
                )
            ]

        records: list[MoneyContextRecord] = []
        for estimate in estimates:
            url = _record_url(estimate)
            value = _first_string(estimate, ("summary", "description", "title", "name")) or "CBO cost estimate published."
            source_links = ()
            if url:
                source_links = (
                    MoneyContextSourceLink(
                        label=_first_string(estimate, ("title", "name")) or "CBO cost estimate",
                        url=url,
                        source_system=self.source.source_id,
                        retrieved_at=retrieved,
                        published_at=_record_datetime(estimate),
                        supports=("money_context", "cbo_cost_estimate"),
                    ),
                )
            records.append(
                MoneyContextRecord(
                    label=_first_string(estimate, ("title", "name")) or "CBO cost estimate",
                    value=value,
                    source_relationship="direct_source" if url else "unavailable",
                    status="available" if url else "unavailable",
                    unavailable_reason=None if url else "CBO estimate record is missing an official URL.",
                    source_links=source_links,
                    source_system=self.source.source_id,
                    metadata={"raw": estimate},
                )
            )
        return records


def money_source_contracts() -> list[dict[str, Any]]:
    """Return source contracts for docs, tests, and future health checks."""

    return [
        {
            "source_id": definition.source_id,
            "label": definition.label,
            "base_url": definition.base_url,
            "identifiers": list(definition.identifiers),
            "source_category": definition.source_category,
            "freshness_expectation": definition.freshness_expectation,
            "unavailable_state": definition.unavailable_state,
            "supported_relationships": list(definition.supported_relationships),
        }
        for definition in MONEY_SOURCE_DEFINITIONS.values()
    ]


def _as_list(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def _first_string(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _record_url(record: dict[str, Any]) -> str | None:
    return _first_string(record, ("source_url", "url", "download_url"))


def _record_datetime(record: dict[str, Any]) -> datetime | None:
    value = record.get("published_at") or record.get("date") or record.get("updated_at")
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None
