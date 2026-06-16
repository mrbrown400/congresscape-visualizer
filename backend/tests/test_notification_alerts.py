from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.models.update import BranchEnum
from app.schemas.notification import AlertCategoryPreferences, FollowedAlertRequest, PushTokenCreate
from app.schemas.update import GovernmentUpdateCreate
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
