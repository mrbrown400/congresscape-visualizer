"""Evidence-backed cross-source links and append-only relationship history."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True, slots=True)
class RelationshipLink:
    left: str
    right: str
    relation: str
    confidence: str
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipAudit:
    operation: str
    subject: str
    targets: tuple[str, ...]
    reason: str
    recorded_at: datetime


class RelationshipGraph:
    def __init__(self) -> None:
        self._links: list[RelationshipLink] = []
        self._audit: list[RelationshipAudit] = []

    def add_link(self, link: RelationshipLink) -> None:
        if link not in self._links:
            self._links.append(link)

    def record_merge(self, subject: str, targets: Iterable[str], reason: str) -> None:
        self._audit.append(RelationshipAudit("merge", subject, tuple(targets), reason, datetime.now(timezone.utc)))

    def record_split(self, subject: str, targets: Iterable[str], reason: str) -> None:
        self._audit.append(RelationshipAudit("split", subject, tuple(targets), reason, datetime.now(timezone.utc)))

    def related(self, subject: str, *, relation: str | None = None) -> tuple[str, ...]:
        graph: dict[str, set[str]] = defaultdict(set)
        for link in self._links:
            if relation is None or link.relation == relation:
                graph[link.left].add(link.right)
                graph[link.right].add(link.left)
        seen = {subject}
        queue = deque([subject])
        while queue:
            current = queue.popleft()
            for target in graph[current]:
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
        return tuple(sorted(seen - {subject}))

    @property
    def links(self) -> tuple[RelationshipLink, ...]:
        return tuple(self._links)

    @property
    def audit(self) -> tuple[RelationshipAudit, ...]:
        return tuple(self._audit)


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
