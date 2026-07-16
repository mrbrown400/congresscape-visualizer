from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.models.update import BranchEnum
from app.models.notification import NotificationDelivery
from app.schemas.notification import AlertCategoryPreferences, FollowedAlertRequest, PushTokenCreate
from app.schemas.update import GovernmentUpdateCreate
from app.schemas.summary import DailyBriefResponse
from app.services.civic_feed_smoke_seed import SMOKE_NOW, seed_civic_feed_smoke
from app.services.notification_service import NotificationService
from app.services.update_service import UpdateService


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_token_persists_followed_objects_and_alert_categories(session) -> None:
    service = NotificationService(session)

    subscription = await service.register_token(
        PushTokenCreate(
            token="ExponentPushToken[deterministic]",
            timezone="America/Los_Angeles",
            followed_bills=["119-hr-1234"],
            followed_members=["R000037"],
            followed_topics=["oversight"],
            followed_committees=["hsgo"],
            alert_categories=AlertCategoryPreferences(money_context=False),
        )
    )

    assert subscription.followed_bills == ["119-hr-1234"]
    assert subscription.followed_members == ["R000037"]
    assert subscription.followed_topics == ["oversight"]
    assert subscription.followed_committees == ["hsgo"]
    assert subscription.alert_categories["money_context"] is False


@pytest.mark.asyncio
async def test_followed_alerts_include_source_backed_categories_and_destinations(session) -> None:
    seed = await seed_civic_feed_smoke(session)

    response = await NotificationService(session).build_followed_alerts(
        FollowedAlertRequest(
            followed_bills=[seed["bill_canonical_id"]],
            followed_members=[seed["member_id"]],
            followed_topics=[seed["topic"]],
            followed_committees=[seed["committee_id"]],
            now=SMOKE_NOW,
            limit=20,
        )
    )

    categories = {item.category for item in response.items}
    assert {"bill_movement", "representative_vote", "hearing_tomorrow", "new_text", "money_context"}.issubset(
        categories
    )
    assert all(item.source_url for item in response.items)
    assert all(item.destination["screen"] == "UpdateDetail" for item in response.items)
    assert any(item.source_url == seed["source_urls"]["vote"] for item in response.items)
    assert any("without inferring motive or intent" in item.body for item in response.items)


@pytest.mark.asyncio
async def test_followed_alerts_respect_category_settings_and_skip_unsourced_money(session) -> None:
    seed = await seed_civic_feed_smoke(session)
    await UpdateService(session).create_update(
        GovernmentUpdateCreate(
            external_id="unsupported-money",
            source="money-context",
            branch=BranchEnum.LEGISLATIVE,
            headline="Unsupported money context should not alert",
            summary="No official money source is attached.",
            full_text=None,
            published_at=datetime(2026, 6, 16, 17, tzinfo=timezone.utc),
            url=None,
            tags=["money"],
            metadata={
                "card_type": "money",
                "bill_canonical_id": seed["bill_canonical_id"],
                "money_context": [
                    {
                        "label": "Unavailable disclosure context",
                        "source_relationship": "unavailable",
                        "source_indexes": [],
                        "unavailable_reason": "No official source attached.",
                    }
                ],
            },
        )
    )
    await session.commit()

    response = await NotificationService(session).build_followed_alerts(
        FollowedAlertRequest(
            followed_bills=[seed["bill_canonical_id"]],
            followed_members=[seed["member_id"]],
            followed_topics=[seed["topic"]],
            followed_committees=[seed["committee_id"]],
            categories=AlertCategoryPreferences(money_context=False),
            now=SMOKE_NOW,
            limit=20,
        )
    )

    assert "money_context" not in {item.category for item in response.items}
    assert all(item.update_id for item in response.items)


@pytest.mark.asyncio
async def test_saved_filters_match_explicit_query_fields(session) -> None:
    service = NotificationService(session)
    device_key = "filter-device"
    await service.save_filter(device_key, "oversight", {"branch": "legislative", "tags": ["oversight"]})
    items = [
        {"headline": "Oversight hearing", "branch": "legislative", "tags": ["oversight", "hearing"]},
        {"headline": "Court opinion", "branch": "judicial", "tags": ["oversight"]},
    ]
    assert [item["headline"] for item in await service.filter_items(device_key, "oversight", items)] == [
        "Oversight hearing"
    ]


@pytest.mark.asyncio
async def test_daily_delivery_is_idempotent_and_retries_failed_batches(session) -> None:
    service = NotificationService(session)
    device_key = "delivery-device"
    await service.register_token(PushTokenCreate(token=device_key))
    brief = DailyBriefResponse(
        summary_date=date(2026, 7, 16),
        generated_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
        headline="Daily brief",
        narrative="A source-backed brief.",
        highlights=[],
        top_updates=[],
    )
    sent: list[list[dict]] = []

    async def sender(payload: list[dict]) -> None:
        sent.append(payload)

    assert await service.dispatch_daily_brief(brief, now=datetime(2026, 7, 16, tzinfo=timezone.utc), sender=sender) == 1
    assert await service.dispatch_daily_brief(brief, now=datetime(2026, 7, 16, 0, 5, tzinfo=timezone.utc), sender=sender) == 0
    assert len(sent) == 1

    retry_brief = brief.model_copy(update={"summary_date": date(2026, 7, 17)})

    async def fail(_payload: list[dict]) -> None:
        raise RuntimeError("temporary transport failure")

    with pytest.raises(RuntimeError, match="temporary transport"):
        await service.dispatch_daily_brief(retry_brief, now=datetime(2026, 7, 17, tzinfo=timezone.utc), sender=fail)
    failed = await session.scalar(select(NotificationDelivery).where(NotificationDelivery.status == "failed"))
    assert failed is not None
    assert failed.attempts == 1
    assert await service.dispatch_daily_brief(
        retry_brief,
        now=failed.next_attempt_at + timedelta(seconds=1),
        sender=sender,
    ) == 1
