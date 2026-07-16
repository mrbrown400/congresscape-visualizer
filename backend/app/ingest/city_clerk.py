"""Narrow, fixture-driven normalizer for Los Angeles City Clerk CFMS records."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

CFMS_RECORD_URL = "https://cityclerk.lacity.org/lacityclerkconnect/index.cfm?cfnumber={cf_number}&fa=ccfi.viewrecord"
PARSER_VERSION = "city-clerk-cfms-1"


@dataclass(frozen=True, slots=True)
class CouncilFileDocument:
    native_id: str
    url: str
    content_type: str
    retrieved_at: datetime
    byte_hash: str
    revision_key: str
    source: str
    state: str = "available"


@dataclass(frozen=True, slots=True)
class CouncilFileEvent:
    event_type: str
    occurred_at: datetime
    text: str
    source: str
    sequence: int


@dataclass(frozen=True, slots=True)
class CouncilFileRecord:
    council_file_number: str
    canonical_url: str
    title: str
    mover: str | None
    seconder: str | None
    district: str | None
    committee: str | None
    department: str | None
    documents: tuple[CouncilFileDocument, ...]
    events: tuple[CouncilFileEvent, ...]
    source_disagreements: tuple[Mapping[str, Any], ...]
    parser_version: str = PARSER_VERSION


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_council_file(payload: Mapping[str, Any]) -> CouncilFileRecord:
    number = str(payload["council_file_number"])
    documents = tuple(
        CouncilFileDocument(
            native_id=str(document["native_id"]),
            url=str(document["url"]),
            content_type=str(document["content_type"]),
            retrieved_at=_date(str(document["retrieved_at"])),
            byte_hash=str(document["byte_hash"]),
            revision_key=str(document.get("revision_key", "1")),
            source=str(document.get("source", "cfms")),
            state=str(document.get("state", "available")),
        )
        for document in payload.get("documents", [])
    )
    events = tuple(
        sorted(
            (
                CouncilFileEvent(
                    event_type=str(event["event_type"]),
                    occurred_at=_date(str(event["occurred_at"])),
                    text=str(event["text"]),
                    source=str(event.get("source", "cfms")),
                    sequence=int(event.get("sequence", index)),
                )
                for index, event in enumerate(payload.get("events", []))
            ),
            key=lambda event: (event.occurred_at, event.sequence),
        )
    )
    return CouncilFileRecord(
        council_file_number=number,
        canonical_url=CFMS_RECORD_URL.format(cf_number=number),
        title=str(payload.get("title", "")),
        mover=payload.get("mover"),
        seconder=payload.get("seconder"),
        district=payload.get("district"),
        committee=payload.get("committee"),
        department=payload.get("department"),
        documents=documents,
        events=events,
        source_disagreements=tuple(payload.get("source_disagreements", [])),
    )
