from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.schemas.update import FeedQueryParams
from app.services.civic_feed_smoke_seed import seed_civic_feed_smoke
from app.services.feed_service import FeedService


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
async def test_deterministic_civic_feed_smoke_seed_covers_mvp_surfaces(session) -> None:
    seed = await seed_civic_feed_smoke(session)

    items, total = await FeedService(session).list_updates(
        FeedQueryParams(
            followed_bills=seed["bill_canonical_id"],
            followed_members=seed["member_id"],
            followed_topics=seed["topic"],
            state="CA",
            district="37",
            limit=10,
        )
    )

    assert total == 5
    by_external_id = {item["external_id"]: item for item in items}
    assert {"bill-action-1", "vote-1", "hearing-1", "text-1", "money-1"} == set(by_external_id)

    vote = by_external_id["vote-1"]
    assert vote["card_type"] == "vote"
    assert vote["detail"]["vote"]["local_representative_positions"][0]["member_identifier"] == seed["member_id"]
    assert vote["detail"]["vote"]["source_url"] == seed["source_urls"]["vote"]

    hearing = by_external_id["hearing-1"]
    assert hearing["card_type"] == "hearing"
    assert hearing["detail"]["hearing"]["follow_supported"] is True
    assert hearing["detail"]["hearing"]["source_url"] == seed["source_urls"]["hearing"]

    bill = by_external_id["bill-action-1"]
    assert bill["card_type"] == "bill"
    assert bill["detail"]["bill"]["vote_eligible"] is True
    assert bill["detail"]["bill"]["user_position_prompt"]
    assert bill["source_trail_status"] == "available"
    assert bill["detail"]["bill"]["source_url"] == seed["source_urls"]["bill"]

    text = by_external_id["text-1"]
    assert text["source_trail"][0]["url"] == seed["source_urls"]["text"]

    money = by_external_id["money-1"]
    assert money["card_type"] == "money"
    assert money["money_context_status"] == "available"
    assert money["money_context"][0]["source_relationship"] == "direct_source"
    assert money["money_context"][0]["source_indexes"]
    assert any(source["url"] == seed["source_urls"]["money"] for source in money["source_trail"])
