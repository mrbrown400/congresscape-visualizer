"""Neutral, source-backed litigation records for fixture and later live adapters."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

LITIGATION_STATUSES = {
    "filed",
    "active",
    "stayed",
    "dismissed",
    "settled",
    "judgment_entered",
    "appealed",
    "sealed",
    "unavailable",
    "duplicate",
    "unverified",
}


@dataclass(frozen=True, slots=True)
class LitigationDocument:
    native_id: str
    document_type: str
    claim_class: str
    source_url: str
    retrieval_time: datetime
    content_hash: str | None
    access_state: str
    revision_of: str | None = None


@dataclass(frozen=True, slots=True)
class LitigationEvent:
    native_id: str
    event_type: str
    occurred_at: datetime
    status: str
    source_url: str


@dataclass(frozen=True, slots=True)
class LitigationCase:
    case_id: str
    court: str
    case_number: str
    title: str
    status: str
    parties: tuple[Mapping[str, Any], ...]
    documents: tuple[LitigationDocument, ...]
    events: tuple[LitigationEvent, ...]
    project_links: tuple[str, ...]
    contract_links: tuple[str, ...]
    original_case_id: str
    confirmed_stakeholder_link: bool
    source_coverage_note: str


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _claim_class(document_type: str) -> str:
    if document_type in {"complaint", "answer", "motion", "brief"}:
        return "allegation" if document_type in {"complaint", "answer"} else "procedural_fact"
    if document_type in {"order", "judgment"}:
        return "ruling"
    if document_type == "settlement":
        return "settlement"
    return "unavailable"


def normalize_litigation_case(payload: Mapping[str, Any]) -> LitigationCase:
    status = str(payload.get("status", "unverified"))
    if status not in LITIGATION_STATUSES:
        status = "unverified"
    documents = tuple(
        LitigationDocument(
            native_id=str(document["native_id"]),
            document_type=str(document["document_type"]),
            claim_class=_claim_class(str(document["document_type"])),
            source_url=str(document["source_url"]),
            retrieval_time=_datetime(str(document["retrieval_time"])),
            content_hash=document.get("content_hash"),
            access_state=str(document.get("access_state", "available")),
            revision_of=document.get("revision_of"),
        )
        for document in payload.get("documents", [])
    )
    events = tuple(
        sorted(
            (
                LitigationEvent(
                    native_id=str(event["native_id"]),
                    event_type=str(event["event_type"]),
                    occurred_at=_datetime(str(event["occurred_at"])),
                    status=str(event.get("status", status)),
                    source_url=str(event["source_url"]),
                )
                for event in payload.get("events", [])
            ),
            key=lambda event: event.occurred_at,
        )
    )
    project_links = tuple(str(value) for value in payload.get("project_links", []))
    contract_links = tuple(str(value) for value in payload.get("contract_links", []))
    party_links = tuple(party for party in payload.get("parties", []) if party.get("verified_stakeholder"))
    return LitigationCase(
        case_id=str(payload["case_id"]),
        court=str(payload["court"]),
        case_number=str(payload["case_number"]),
        title=str(payload.get("title", "")),
        status=status,
        parties=tuple(payload.get("parties", [])),
        documents=documents,
        events=events,
        project_links=project_links,
        contract_links=contract_links,
        original_case_id=str(payload.get("original_case_id", payload["case_id"])),
        confirmed_stakeholder_link=bool(project_links or contract_links or party_links),
        source_coverage_note=str(payload.get("source_coverage_note", "Court/date coverage is not exhaustive.")),
    )


def candidate_is_confirmed(payload: Mapping[str, Any]) -> bool:
    """Require a party or explicit project/contract link; keywords alone do not confirm a case."""
    return bool(
        payload.get("project_links")
        or payload.get("contract_links")
        or any(party.get("verified_stakeholder") for party in payload.get("parties", []))
    )
