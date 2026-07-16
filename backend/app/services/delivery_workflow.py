"""Deterministic query and delivery primitives shared by notification workflows."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


def matches_saved_filter(item: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Apply only explicit feed filters; an absent filter does not narrow results."""

    search = str(filters.get("search") or "").strip().lower()
    if search and search not in f"{item.get('headline', '')} {item.get('summary', '')}".lower():
        return False
    branch = filters.get("branch")
    if branch and str(item.get("branch", "")).lower() != str(branch).lower():
        return False
    source = filters.get("source")
    if source and str(item.get("source", "")).lower() != str(source).lower():
        return False
    tags = {str(value).lower() for value in item.get("tags") or []}
    required_tags = {str(value).lower() for value in filters.get("tags") or []}
    return not required_tags or required_tags.issubset(tags)


def delivery_dedupe_key(batch_key: str, token: str) -> str:
    return hashlib.sha256(f"{batch_key}:{token}".encode("utf-8")).hexdigest()


def retry_at(now: datetime, attempts: int) -> datetime:
    """Bound exponential retry delay to keep failed scheduled batches recoverable."""

    delay_minutes = min(60, 2 ** max(attempts - 1, 0))
    return now.astimezone(timezone.utc) + timedelta(minutes=delay_minutes)


def batch_key_for_date(target_date: datetime) -> str:
    return f"daily:{target_date.astimezone(timezone.utc).date().isoformat()}"


def unique_tokens(subscriptions: Iterable[Any]) -> list[str]:
    values = (getattr(subscription, "token", subscription) for subscription in subscriptions)
    return list(dict.fromkeys(str(token) for token in values if token))
