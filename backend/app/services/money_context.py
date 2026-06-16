"""Source-labeled money context assembly for civic cards."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.ingest.money import (
    CBOBillCostEstimateAdapter,
    MONEY_SOURCE_DEFINITIONS,
    MoneyContextRecord,
    MoneySourceRelationship,
)

MoneyContextStatus = str

RELATIONSHIP_LABELS: dict[MoneySourceRelationship, str] = {
    "direct_source": "Direct source match",
    "related_entity": "Related entity context",
    "topic_context": "Topic or industry context",
    "unavailable": "Unavailable",
}

RELATIONSHIP_DESCRIPTIONS: dict[MoneySourceRelationship, str] = {
    "direct_source": "The source directly names this bill, member, committee, or record.",
    "related_entity": "The source names an organization, person, or committee related to this card.",
    "topic_context": "The source is related by topic or industry and is shown only as context.",
    "unavailable": "No sourced money context is available for this card yet.",
}

NO_INFERENCE_NOTE = "Money context is source-backed context only; it does not imply corruption, motive, or intent."


def confidence_label(relationship: str | None) -> dict[str, str]:
    normalized = normalize_relationship(relationship)
    return {
        "relationship": normalized,
        "label": RELATIONSHIP_LABELS[normalized],
        "description": RELATIONSHIP_DESCRIPTIONS[normalized],
    }


def normalize_relationship(value: str | None) -> MoneySourceRelationship:
    if value in RELATIONSHIP_LABELS:
        return value
    return "unavailable"


def money_source_contracts_by_id() -> dict[str, dict[str, Any]]:
    return {
        source_id: {
            "label": definition.label,
            "base_url": definition.base_url,
            "identifiers": list(definition.identifiers),
            "freshness_expectation": definition.freshness_expectation,
            "unavailable_state": definition.unavailable_state,
            "supported_relationships": list(definition.supported_relationships),
        }
        for source_id, definition in MONEY_SOURCE_DEFINITIONS.items()
    }


def money_source_trail_from_payload(raw_items: Any, *, retrieved_at: datetime | None = None) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for item in _as_list(raw_items):
        source_relationship = normalize_relationship(_string(item.get("source_relationship")) or _string(item.get("confidence")))
        source_system = _string(item.get("source_system")) or _string(item.get("source")) or "money_context"
        source_category = _string(item.get("source_category")) or ("unavailable" if source_relationship == "unavailable" else "official")
        source_label = _string(item.get("source_label")) or _string(item.get("label")) or source_system
        supports = item.get("supports") if isinstance(item.get("supports"), list) else ["money_context"]

        for url in _source_urls(item):
            links.append(
                {
                    "label": source_label,
                    "source": source_system,
                    "url": url,
                    "published_at": item.get("published_at"),
                    "retrieved_at": item.get("retrieved_at") or retrieved_at,
                    "supports": supports,
                    "confidence": source_relationship,
                    "source_category": source_category,
                }
            )
    return _dedupe_sources(links)


def money_source_trail_from_cbo_estimates(estimates: Any, *, retrieved_at: datetime | None = None) -> list[dict[str, Any]]:
    records = CBOBillCostEstimateAdapter().normalize(
        {"cbo_cost_estimates": _as_list(estimates)},
        retrieved_at=retrieved_at,
    )
    links: list[dict[str, Any]] = []
    for record in records:
        for source_link in record.source_links:
            payload = source_link.as_source_link_payload()
            links.append(
                {
                    "label": payload["label"],
                    "source": payload["source_system"],
                    "url": payload["url"],
                    "published_at": payload["published_at"],
                    "retrieved_at": payload["retrieved_at"],
                    "supports": payload["supports"],
                    "confidence": payload["confidence"],
                    "source_category": payload["source_category"],
                }
            )
    return _dedupe_sources(links)


def build_bill_money_context(
    *,
    bill_metadata: dict[str, Any] | None,
    cbo_cost_estimates: Any,
    source_trail: list[dict[str, Any]],
) -> dict[str, Any]:
    metadata_items = _as_list((bill_metadata or {}).get("money_context"))
    records = [*_records_from_payload(metadata_items)]
    if not records:
        records = CBOBillCostEstimateAdapter().normalize({"cbo_cost_estimates": _as_list(cbo_cost_estimates)})

    return build_money_context(records, source_trail, unavailable_note="No sourced money context is attached for this bill yet.")


def build_member_money_context(
    *,
    member_metadata: dict[str, Any] | None,
    source_trail: list[dict[str, Any]],
) -> dict[str, Any]:
    records = _records_from_payload(_as_list((member_metadata or {}).get("money_context")))
    return build_money_context(
        records,
        source_trail,
        unavailable_note="No sourced member disclosure context is attached yet.",
    )


def build_payload_money_context(
    raw_items: Any,
    source_trail: list[dict[str, Any]],
    *,
    unavailable_note: str,
) -> dict[str, Any]:
    return build_money_context(
        _records_from_payload(_as_list(raw_items)),
        source_trail,
        unavailable_note=unavailable_note,
    )


def build_money_context(
    records: list[MoneyContextRecord],
    source_trail: list[dict[str, Any]],
    *,
    unavailable_note: str,
) -> dict[str, Any]:
    items = [_money_item(record, source_trail) for record in records]
    available_items = [
        item
        for item in items
        if item["source_relationship"] != "unavailable" and item["source_indexes"]
    ]
    pending_items = [item for item in items if item.get("status") == "pending"]

    if available_items:
        status: MoneyContextStatus = "available"
        note = NO_INFERENCE_NOTE
    elif pending_items:
        status = "pending"
        note = "Money context is pending source retrieval. " + NO_INFERENCE_NOTE
    else:
        status = "unavailable"
        note = unavailable_note

    return {
        "money_context_status": status,
        "money_context_note": note,
        "money_context": items if items else [],
    }


def _money_item(record: MoneyContextRecord, source_trail: list[dict[str, Any]]) -> dict[str, Any]:
    source_urls = [source.url for source in record.source_links]
    source_indexes = _source_indexes(source_trail, source_urls)
    relationship = normalize_relationship(record.source_relationship)
    unavailable_reason = record.unavailable_reason
    if relationship != "unavailable" and not source_indexes:
        unavailable_reason = unavailable_reason or "No source-trail entry is attached for this money context."

    return {
        "label": record.label,
        "value": record.value,
        "source_relationship": relationship,
        "confidence_label": confidence_label(relationship),
        "source_indexes": source_indexes,
        "unavailable_reason": unavailable_reason,
        "note": record.note or NO_INFERENCE_NOTE,
        "status": record.status,
        "source_system": record.source_system,
        "source_category": record.source_category,
    }


def _records_from_payload(items: list[dict[str, Any]]) -> list[MoneyContextRecord]:
    records: list[MoneyContextRecord] = []
    for item in items:
        relationship = normalize_relationship(
            _string(item.get("source_relationship")) or _string(item.get("confidence"))
        )
        source_system = _string(item.get("source_system")) or _string(item.get("source")) or "money_context"
        source_category = _string(item.get("source_category")) or (
            "unavailable" if relationship == "unavailable" else "official"
        )
        links = []
        for source in money_source_trail_from_payload([item]):
            links.append(
                {
                    "label": source["label"],
                    "url": source["url"],
                    "source_system": source["source"],
                    "retrieved_at": source.get("retrieved_at"),
                    "published_at": source.get("published_at"),
                    "supports": source.get("supports") or ["money_context"],
                    "confidence": source.get("confidence") or relationship,
                    "source_category": source.get("source_category") or source_category,
                }
            )

        source_links = tuple(
            _source_link_from_dict(link)
            for link in links
            if isinstance(link.get("url"), str) and isinstance(link.get("source_system"), str)
        )
        records.append(
            MoneyContextRecord(
                label=_string(item.get("label")) or "Money context",
                value=_string(item.get("value")),
                source_relationship=relationship,
                status=_string(item.get("status")) or ("unavailable" if relationship == "unavailable" else "available"),
                note=_string(item.get("note")),
                unavailable_reason=_string(item.get("unavailable_reason")),
                source_links=source_links,
                source_system=source_system,
                source_category=source_category,
                metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
            )
        )
    return records


def _source_link_from_dict(link: dict[str, Any]):
    from app.ingest.money import MoneyContextSourceLink

    retrieved_at = link.get("retrieved_at")
    if not isinstance(retrieved_at, datetime):
        retrieved_at = datetime.now(timezone.utc)

    return MoneyContextSourceLink(
        label=link["label"],
        url=link["url"],
        source_system=link["source_system"],
        retrieved_at=retrieved_at,
        published_at=link.get("published_at") if isinstance(link.get("published_at"), datetime) else None,
        supports=tuple(str(value) for value in link.get("supports", ["money_context"])),
        confidence=normalize_relationship(_string(link.get("confidence"))),
        source_category=_string(link.get("source_category")) or "official",
    )


def _source_indexes(source_trail: list[dict[str, Any]], urls: list[str]) -> list[int]:
    indexes: list[int] = []
    url_set = {url for url in urls if url}
    for index, source in enumerate(source_trail):
        if source.get("url") in url_set:
            indexes.append(index)
    return indexes


def _source_urls(item: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for key in ("source_url", "url"):
        value = item.get(key)
        if isinstance(value, str) and value:
            urls.append(value)
    raw_urls = item.get("source_urls")
    if isinstance(raw_urls, list):
        urls.extend(str(value) for value in raw_urls if value)
    raw_links = item.get("source_links")
    if isinstance(raw_links, list):
        for link in raw_links:
            if isinstance(link, dict) and isinstance(link.get("url"), str):
                urls.append(link["url"])
    return list(dict.fromkeys(urls))


def _as_list(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def _string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str | None, str | None]] = set()
    deduped: list[dict[str, Any]] = []
    for source in sources:
        key = (source.get("source"), source.get("url"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped
