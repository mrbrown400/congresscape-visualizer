"""Evidence-backed cross-source links and append-only relationship history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class RelationshipLink:
    left: str
    right: str
    relation: str
    confidence: str
    evidence: tuple[str, ...]


def exact_identifier_links(
    left: dict[str, str], right: dict[str, str], *, relation: str, evidence: str
) -> tuple[RelationshipLink, ...]:
    links = []
    for key, value in left.items():
        if value and right.get(key) == value:
            links.append(RelationshipLink(left["id"], right["id"], relation, "exact", (f"{key}={value}", evidence)))
    return tuple(links)


def candidate_link(left_id: str, right_id: str, relation: str, evidence: Iterable[str]) -> RelationshipLink:
    return RelationshipLink(left_id, right_id, relation, "candidate", tuple(evidence))
