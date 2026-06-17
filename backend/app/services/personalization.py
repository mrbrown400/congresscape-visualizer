"""Source-transparent ranking logic for primary-source feed events."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from app.models.update import GovernmentUpdate


def rank_updates(updates: Sequence[GovernmentUpdate], context: dict | None = None) -> list[GovernmentUpdate]:
    """Return updates sorted by civic relevance without engagement heuristics."""

    return sorted(
        list(updates),
        key=lambda update: score_update(update, context=context),
        reverse=True,
    )


def score_update(update: GovernmentUpdate, context: dict | None = None) -> float:
    """Score an update using auditable primary-source factors."""

    factors = ranking_factors(update, context=context)
    return float(sum(factors.values()))


def ranking_factors(update: GovernmentUpdate, context: dict | None = None) -> dict[str, float]:
    """Explainable scoring factors used by Today and feed ranking."""

    context = context or {}
    metadata = update.metadata_json or {}
    tags = {str(tag).lower() for tag in (update.tags or [])}
    now = _context_now(context)

    return {
        "source_freshness": _freshness_score(update, now),
        "lifecycle_importance": _lifecycle_score(update, metadata, tags),
        "local_relevance": _local_relevance_score(update, context, metadata),
        "followed_object_relevance": _followed_object_score(update, context, metadata),
        "source_transparency": _source_transparency_score(update, metadata),
    }


def _context_now(context: dict[str, Any]) -> datetime:
    value = context.get("now")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _freshness_score(update: GovernmentUpdate, now: datetime) -> float:
    published_at = update.published_at
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    age_hours = max((now - published_at).total_seconds() / 3600, 0)
    if age_hours <= 6:
        return 30
    if age_hours <= 24:
        return 22
    if age_hours <= 72:
        return 12
    return 4


def _lifecycle_score(update: GovernmentUpdate, metadata: dict[str, Any], tags: set[str]) -> float:
    event_type = str(metadata.get("event_type") or metadata.get("card_type") or "").lower()
    action_type = str(metadata.get("action_type") or "").lower()
    status = str(metadata.get("status") or "").lower()

    if update.vote_id or event_type == "vote" or "vote" in tags:
        return 35
    if update.hearing_id or event_type == "hearing" or "hearing" in tags:
        return 28
    if event_type in {"text_version", "new_text"} or "text" in tags:
        return 24
    if any(term in action_type or term in status for term in ("passed", "law", "president", "committee")):
        return 22
    if update.bill_action_id or event_type in {"bill_action", "bill"} or "bill" in tags:
        return 18
    return 8


def _local_relevance_score(update: GovernmentUpdate, context: dict[str, Any], metadata: dict[str, Any]) -> float:
    state = _normalized(context.get("state"))
    district = _normalized(context.get("district"))
    if not state:
        return 0

    update_states = {_normalized(value) for value in _metadata_values(metadata, "states")}
    update_districts = {_normalized(value) for value in _metadata_values(metadata, "districts")}
    member_states = {
        _normalized(member.get("state"))
        for member in _metadata_values(metadata, "members")
        if isinstance(member, dict)
    }
    member_districts = {
        _normalized(member.get("district"))
        for member in _metadata_values(metadata, "members")
        if isinstance(member, dict)
    }

    score = 0.0
    if state in update_states or state in member_states:
        score += 12
    if district and (district in update_districts or district in member_districts):
        score += 10
    return score


def _followed_object_score(update: GovernmentUpdate, context: dict[str, Any], metadata: dict[str, Any]) -> float:
    followed_bills = _normalized_set(context.get("followed_bills"))
    followed_members = _normalized_set(context.get("followed_members"))
    followed_topics = _normalized_set(context.get("followed_topics"))
    followed_committees = _normalized_set(context.get("followed_committees"))

    bill_ids = {
        _normalized(value)
        for value in [update.bill_id, metadata.get("bill_id"), metadata.get("bill_canonical_id")]
        if value is not None
    }
    bill = getattr(update, "bill", None)
    if bill is not None:
        bill_ids.add(_normalized(getattr(bill, "canonical_id", "")))
    vote = getattr(update, "vote", None)
    vote_bill = getattr(vote, "bill", None) if vote is not None else None
    if vote_bill is not None:
        bill_ids.add(_normalized(getattr(vote_bill, "canonical_id", "")))
    member_ids = {
        _normalized(value)
        for value in _metadata_values(metadata, "member_ids")
        if value is not None
    }
    member_ids.update(
        _normalized(member.get("bioguide_id") or member.get("id"))
        for member in _metadata_values(metadata, "members")
        if isinstance(member, dict)
    )
    topic_values = {_normalized(tag) for tag in (update.tags or [])}
    topic_values.update(_normalized(value) for value in _metadata_values(metadata, "topics"))
    topic_values.update(_normalized(value.get("name")) for value in _metadata_values(metadata, "subjects") if isinstance(value, dict))
    committee_ids = {
        _normalized(value)
        for value in _metadata_values(metadata, "committee_ids")
        if value is not None
    }
    committee_ids.update(
        _normalized(committee.get("committee_code") or committee.get("id") or committee.get("name"))
        for committee in _metadata_values(metadata, "committees")
        if isinstance(committee, dict)
    )
    hearing = getattr(update, "hearing", None)
    hearing_committee = getattr(hearing, "committee", None) if hearing is not None else None
    if hearing_committee is not None:
        committee_ids.add(_normalized(getattr(hearing_committee, "committee_code", "")))
    if bill is not None:
        committee_ids.update(_normalized(getattr(committee, "committee_code", "")) for committee in bill.committees)

    score = 0.0
    if followed_bills and followed_bills.intersection(bill_ids):
        score += 18
    if followed_members and followed_members.intersection(member_ids):
        score += 15
    if followed_topics and followed_topics.intersection(topic_values):
        score += 10
    if followed_committees and followed_committees.intersection(committee_ids):
        score += 10
    return score


def _source_transparency_score(update: GovernmentUpdate, metadata: dict[str, Any]) -> float:
    source_trail = metadata.get("source_trail")
    if isinstance(source_trail, list) and source_trail:
        return 10
    if update.url:
        return 8
    return 0


def _metadata_values(metadata: dict[str, Any], key: str) -> list[Any]:
    value = metadata.get(key)
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _normalized_set(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    if isinstance(value, str):
        return {_normalized(item) for item in value.split(",") if item.strip()}
    if isinstance(value, Sequence):
        return {_normalized(item) for item in value if item not in (None, "")}
    return {_normalized(value)}


def _normalized(value: Any) -> str:
    return str(value).strip().lower()
