"""Store Expo push tokens and deliver daily brief notifications."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Iterable, Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationBatch, NotificationDelivery, NotificationSubscription, SavedFeedFilter
from app.models.update import GovernmentUpdate
from app.schemas.notification import FollowedAlertRead, FollowedAlertRequest, FollowedAlertResponse, PushTokenCreate
from app.schemas.summary import DailyBriefResponse
from app.schemas.update import FeedQueryParams
from app.services.feed_service import FeedService
from app.services.delivery_workflow import batch_key_for_date, delivery_dedupe_key, matches_saved_filter, retry_at, unique_tokens


class NotificationService:
    """Persist device push tokens and fan out summary alerts via Expo."""

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_token(self, payload: PushTokenCreate) -> NotificationSubscription:
        subscription = NotificationSubscription(
            token=payload.token,
            platform=payload.platform,
            timezone=payload.timezone,
            followed_bills=payload.followed_bills,
            followed_members=payload.followed_members,
            followed_topics=payload.followed_topics,
            followed_committees=payload.followed_committees,
            alert_categories=payload.alert_categories.model_dump(),
            delivery_preferences=payload.delivery_preferences,
        )
        self.session.add(subscription)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # Update existing row with the latest metadata instead.
            existing = await self._get_by_token(payload.token)
            if existing:
                existing.platform = payload.platform
                existing.timezone = payload.timezone
                existing.followed_bills = payload.followed_bills
                existing.followed_members = payload.followed_members
                existing.followed_topics = payload.followed_topics
                existing.followed_committees = payload.followed_committees
                existing.alert_categories = payload.alert_categories.model_dump()
                existing.delivery_preferences = payload.delivery_preferences
                self.session.add(existing)
                await self.session.commit()
                await self.session.refresh(existing)
                return existing
            raise
        await self.session.refresh(subscription)
        return subscription

    async def _get_by_token(self, token: str) -> NotificationSubscription | None:
        stmt = select(NotificationSubscription).where(NotificationSubscription.token == token)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_filter(self, token: str, name: str, filters: dict[str, Any]) -> SavedFeedFilter:
        """Create or replace a named device-scoped saved filter."""

        record = await self.session.scalar(
            select(SavedFeedFilter).where(SavedFeedFilter.token == token, SavedFeedFilter.name == name)
        )
        if record is None:
            record = SavedFeedFilter(token=token, name=name, filters=filters)
            self.session.add(record)
        else:
            record.filters = filters
            record.enabled = True
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_filters(self, token: str) -> list[SavedFeedFilter]:
        result = await self.session.execute(
            select(SavedFeedFilter).where(SavedFeedFilter.token == token, SavedFeedFilter.enabled.is_(True)).order_by(SavedFeedFilter.name)
        )
        return list(result.scalars().all())

    async def filter_items(self, token: str, name: str, items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        record = await self.session.scalar(
            select(SavedFeedFilter).where(SavedFeedFilter.token == token, SavedFeedFilter.name == name, SavedFeedFilter.enabled.is_(True))
        )
        if record is None:
            return []
        return [item for item in items if matches_saved_filter(item, record.filters or {})]

    async def dispatch_daily_brief(
        self,
        brief: DailyBriefResponse,
        *,
        now: datetime | None = None,
        sender: Callable[[list[dict[str, Any]]], Awaitable[None]] | None = None,
    ) -> int:
        """Deliver one idempotent batch, recording failures for exponential retry."""

        tokens = await self._all_tokens()
        if not tokens:
            return 0

        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        batch_key = batch_key_for_date(datetime.combine(brief.summary_date, datetime.min.time(), tzinfo=timezone.utc))
        batch = await self.session.scalar(select(NotificationBatch).where(NotificationBatch.batch_key == batch_key))
        if batch is None:
            batch = NotificationBatch(batch_key=batch_key, scheduled_for=current, status="pending")
            self.session.add(batch)
            await self.session.flush()

        due: list[NotificationDelivery] = []
        for token in unique_tokens(tokens):
            dedupe_key = delivery_dedupe_key(batch_key, token)
            delivery = await self.session.scalar(
                select(NotificationDelivery).where(NotificationDelivery.dedupe_key == dedupe_key)
            )
            if delivery is None:
                delivery = NotificationDelivery(
                    batch_id=batch.id,
                    token=token,
                    dedupe_key=dedupe_key,
                    payload=self._build_push_payload([token], brief)[0],
                )
                self.session.add(delivery)
            elif delivery.status == "sent":
                continue
            elif delivery.next_attempt_at and _aware(delivery.next_attempt_at) > current:
                continue
            due.append(delivery)

        if not due:
            await self.session.commit()
            return 0

        payload = [delivery.payload for delivery in due]
        try:
            if sender is not None:
                await sender(payload)
            else:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(self.EXPO_PUSH_URL, json=payload)
                    response.raise_for_status()
        except Exception as exc:
            batch.status = "failed"
            batch.attempts = (batch.attempts or 0) + 1
            batch.last_error = str(exc)[:500]
            batch.next_attempt_at = retry_at(current, batch.attempts)
            for delivery in due:
                delivery.status = "failed"
                delivery.attempts = (delivery.attempts or 0) + 1
                delivery.last_error = str(exc)[:500]
                delivery.next_attempt_at = retry_at(current, delivery.attempts)
            await self.session.commit()
            raise

        sent_at = current
        for delivery in due:
            delivery.status = "sent"
            delivery.sent_at = sent_at
            delivery.next_attempt_at = None
        batch.status = "completed"
        batch.completed_at = sent_at
        await self.session.execute(
            NotificationSubscription.__table__.update()
            .where(NotificationSubscription.token.in_([delivery.token for delivery in due]))
            .values(last_notified_at=sent_at)
        )
        await self.session.commit()
        return len(due)

    async def _all_tokens(self) -> Sequence[str]:
        stmt = select(NotificationSubscription.token)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def build_followed_alerts(self, request: FollowedAlertRequest) -> FollowedAlertResponse:
        """Build source-backed alerts from recent feed records and local follow state."""

        stmt = select(GovernmentUpdate).order_by(GovernmentUpdate.published_at.desc()).limit(request.limit * 5)
        result = await self.session.execute(stmt)
        feed_service = FeedService(self.session)
        params = FeedQueryParams(
            followed_bills=",".join(request.followed_bills) or None,
            followed_members=",".join(request.followed_members) or None,
            followed_topics=",".join(request.followed_topics) or None,
            limit=request.limit,
        )

        alerts: list[FollowedAlertRead] = []
        for update in result.scalars().all():
            item = feed_service._to_feed_item(update, params)
            alerts.extend(self._alerts_for_item(item, request, request.now))
            if len(alerts) >= request.limit:
                break

        return FollowedAlertResponse(items=alerts[: request.limit], total=len(alerts[: request.limit]))

    def _build_push_payload(self, tokens: Iterable[str], brief: DailyBriefResponse) -> list[dict[str, str]]:
        title = brief.headline
        body = brief.narrative if len(brief.narrative) < 220 else brief.narrative[:217] + "..."

        return [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": {
                    "summary_date": brief.summary_date.isoformat(),
                    "headline": title,
                },
            }
            for token in tokens
        ]

    def _alerts_for_item(
        self,
        item: dict[str, Any],
        request: FollowedAlertRequest,
        now: datetime | None,
    ) -> list[FollowedAlertRead]:
        source = _first_source(item)
        source_url = _string(source.get("url")) if source else _string(item.get("url"))
        if not source_url:
            return []

        categories = request.categories
        matches = _match_reasons(item, request)
        if not matches:
            return []

        alerts: list[FollowedAlertRead] = []
        card_type = _string(item.get("card_type"))
        tags = _normalized_set(item.get("tags"))
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        event_type = _normalized(metadata.get("event_type") or metadata.get("card_type"))

        if categories.representative_votes and card_type == "vote" and any(reason.startswith("member:") for reason in matches):
            alerts.append(self._alert(item, "representative_vote", source_url, source, "Your representative voted", matches))

        if categories.hearing_tomorrow and card_type == "hearing" and _is_tomorrow(item, now):
            if any(reason.startswith(("committee:", "topic:")) for reason in matches):
                alerts.append(self._alert(item, "hearing_tomorrow", source_url, source, "Hearing tomorrow", matches))

        if categories.new_text and (event_type in {"text_version", "new_text"} or "text" in tags):
            if any(reason.startswith("bill:") for reason in matches):
                alerts.append(self._alert(item, "new_text", source_url, source, "New bill text", matches))

        if categories.money_context and _has_supported_money_context(item):
            alerts.append(self._alert(item, "money_context", source_url, source, "Money context updated", matches))

        is_bill_movement = card_type == "bill" or item.get("bill_action_id") is not None or "lifecycle" in tags
        if categories.bill_movement and is_bill_movement and any(reason.startswith(("bill:", "topic:")) for reason in matches):
            alerts.append(self._alert(item, "bill_movement", source_url, source, "Bill movement", matches))

        return alerts

    def _alert(
        self,
        item: dict[str, Any],
        category: str,
        source_url: str,
        source: dict[str, Any] | None,
        title: str,
        match_reasons: list[str],
    ) -> FollowedAlertRead:
        return FollowedAlertRead(
            category=category,  # type: ignore[arg-type]
            title=title,
            body=_body_for_category(category, item),
            update_id=int(item["id"]),
            source_url=source_url,
            source_label=_string(source.get("label")) if source else None,
            published_at=item["published_at"],
            event_date=item.get("event_date"),
            destination={
                "screen": "UpdateDetail",
                "update_id": item["id"],
                "card_type": item.get("card_type"),
                "source_url": source_url,
            },
            match_reasons=match_reasons,
        )


def _match_reasons(item: dict[str, Any], request: FollowedAlertRequest) -> list[str]:
    reasons: list[str] = []
    followed_bills = _normalized_set(request.followed_bills)
    followed_members = _normalized_set(request.followed_members)
    followed_topics = _normalized_set(request.followed_topics)
    followed_committees = _normalized_set(request.followed_committees)

    for bill_id in _bill_ids(item):
        if bill_id in followed_bills:
            reasons.append(f"bill:{bill_id}")
    for member_id in _member_ids(item):
        if member_id in followed_members:
            reasons.append(f"member:{member_id}")
    for topic in _topic_values(item):
        if topic in followed_topics:
            reasons.append(f"topic:{topic}")
    for committee_id in _committee_ids(item):
        if committee_id in followed_committees:
            reasons.append(f"committee:{committee_id}")

    return list(dict.fromkeys(reasons))


def _bill_ids(item: dict[str, Any]) -> set[str]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    ids = {_normalized(value) for value in (item.get("bill_id"), metadata.get("bill_id"), metadata.get("bill_canonical_id")) if value}
    bill = ((item.get("detail") or {}).get("bill") or {}) if isinstance(item.get("detail"), dict) else {}
    if isinstance(bill, dict):
        ids.update(_normalized(value) for value in (bill.get("canonical_id"), bill.get("display_number")) if value)
    return ids


def _member_ids(item: dict[str, Any]) -> set[str]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    ids = {_normalized(value) for value in _metadata_values(metadata, "member_ids")}
    ids.update(_normalized(member.get("bioguide_id") or member.get("id")) for member in _metadata_values(metadata, "members") if isinstance(member, dict))
    vote = ((item.get("detail") or {}).get("vote") or {}) if isinstance(item.get("detail"), dict) else {}
    if isinstance(vote, dict):
        for position in vote.get("positions") or []:
            if isinstance(position, dict):
                ids.add(_normalized(position.get("member_identifier")))
    return {value for value in ids if value}


def _topic_values(item: dict[str, Any]) -> set[str]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    values = _normalized_set(item.get("tags"))
    values.update(_normalized(value) for value in _metadata_values(metadata, "topics"))
    values.update(_normalized(value.get("name")) for value in _metadata_values(metadata, "subjects") if isinstance(value, dict))
    return {value for value in values if value}


def _committee_ids(item: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
    hearing = detail.get("hearing") if isinstance(detail, dict) else {}
    if isinstance(hearing, dict) and isinstance(hearing.get("committee"), dict):
        committee = hearing["committee"]
        ids.update(_normalized(value) for value in (committee.get("committee_code"), committee.get("name")) if value)
    bill = detail.get("bill") if isinstance(detail, dict) else {}
    if isinstance(bill, dict):
        for committee in bill.get("committees") or []:
            if isinstance(committee, dict):
                ids.update(_normalized(value) for value in (committee.get("committee_code"), committee.get("name")) if value)
    return {value for value in ids if value}


def _first_source(item: dict[str, Any]) -> dict[str, Any] | None:
    preferred_url = _detail_source_url(item)
    source_trail = item.get("source_trail")
    if isinstance(source_trail, list):
        for source in source_trail:
            if isinstance(source, dict) and preferred_url and source.get("url") == preferred_url:
                return source
        for source in source_trail:
            if isinstance(source, dict) and source.get("url"):
                return source
    if preferred_url:
        return {"label": "Official source", "url": preferred_url}
    return None


def _detail_source_url(item: dict[str, Any]) -> str | None:
    detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
    if isinstance(detail, dict):
        for key in ("vote", "hearing", "bill"):
            value = detail.get(key)
            if isinstance(value, dict):
                source_url = _string(value.get("source_url"))
                if source_url:
                    return source_url
    return None


def _is_tomorrow(item: dict[str, Any], now: datetime | None) -> bool:
    event_date = _parse_datetime(item.get("event_date"))
    if not event_date:
        detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
        hearing = detail.get("hearing") if isinstance(detail, dict) else {}
        if isinstance(hearing, dict):
            event_date = _parse_datetime(hearing.get("scheduled_at"))
    if not event_date:
        return False
    current = _aware(now or datetime.now(timezone.utc))
    event_date = _aware(event_date)
    return current <= event_date <= current + timedelta(days=1)


def _has_supported_money_context(item: dict[str, Any]) -> bool:
    if item.get("money_context_status") != "available":
        return False
    for record in item.get("money_context") or []:
        if not isinstance(record, dict):
            continue
        relationship = _normalized(record.get("source_relationship"))
        if relationship and relationship != "unavailable" and record.get("source_indexes"):
            return True
    return False


def _body_for_category(category: str, item: dict[str, Any]) -> str:
    headline = _string(item.get("headline")) or "A followed source-backed event changed."
    if category == "representative_vote":
        return f"{headline} Official roll-call source is attached."
    if category == "hearing_tomorrow":
        return f"{headline} The official hearing notice links to the detail page."
    if category == "new_text":
        return f"{headline} New official bill text is available."
    if category == "money_context":
        return f"{headline} Sourced money context changed without inferring motive or intent."
    return f"{headline} Open the source-backed card for details."


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
    return str(value or "").strip().lower()


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
