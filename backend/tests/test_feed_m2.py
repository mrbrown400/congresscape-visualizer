from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.models.legislative import BillAction
from app.models.update import BranchEnum
from app.schemas.update import FeedQueryParams, GovernmentUpdateCreate
from app.services.feed_service import FeedService
from app.services.legislative_service import LegislativeDataService
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
async def test_today_feed_ranks_canonical_primary_source_events_with_detail_payloads(session) -> None:
    now = datetime(2026, 6, 16, 18, tzinfo=timezone.utc)
    legislative = LegislativeDataService(session)
    updates = UpdateService(session)

    await legislative.upsert_member(
        {
            "bioguide_id": "R000037",
            "name": "CA 37 Representative",
            "party": "D",
            "state": "CA",
            "district": "37",
            "chamber": "House",
            "congress_url": "https://www.congress.gov/member/ca-37-representative/R000037",
        }
    )
    bill = await legislative.upsert_bill(
        {
            "congress": 119,
            "bill_type": "hr",
            "number": "1234",
            "title": "Civic Data Transparency Act",
            "short_title": "Civic Data Transparency Act",
            "introduced_at": now - timedelta(days=10),
            "latest_action_at": now - timedelta(hours=18),
            "latest_action_text": "Passed House.",
            "policy_area": "Government Operations and Politics",
            "congress_url": "https://www.congress.gov/bill/119th-congress/house-bill/1234",
            "cosponsors": [{"name": "Example Cosponsor"}],
            "actions": [
                {
                    "sequence": 1,
                    "action_type": "Passed House",
                    "text": "Passed/agreed to in House.",
                    "acted_at": now - timedelta(hours=18),
                    "chamber": "House",
                    "source_url": "https://www.congress.gov/bill/119th-congress/house-bill/1234/actions",
                    "source_links": [
                        {
                            "label": "Congress.gov action",
                            "url": "https://www.congress.gov/bill/119th-congress/house-bill/1234/actions",
                            "source_system": "congress.gov",
                            "retrieved_at": now,
                            "supports": ["bill action"],
                        }
                    ],
                }
            ],
            "text_versions": [
                {
                    "version_code": "ih",
                    "version_name": "Introduced in House",
                    "published_at": now - timedelta(days=10),
                    "source_url": "https://www.congress.gov/bill/119th-congress/house-bill/1234/text/ih",
                }
            ],
            "committees": [
                {
                    "committee_code": "hsgo",
                    "name": "House Oversight and Accountability",
                    "chamber": "House",
                    "jurisdiction": "Government operations oversight.",
                    "congress_url": "https://www.congress.gov/committee/house-oversight-and-accountability/hsgo",
                }
            ],
            "source_links": [
                {
                    "label": "Congress.gov bill",
                    "url": "https://www.congress.gov/bill/119th-congress/house-bill/1234",
                    "source_system": "congress.gov",
                    "retrieved_at": now,
                    "supports": ["bill"],
                }
            ],
        }
    )
    action = (await session.execute(select(BillAction))).scalars().first()
    vote = await legislative.upsert_vote(
        {
            "chamber": "House",
            "congress": 119,
            "session": "2",
            "roll_number": "42",
            "vote_date": now - timedelta(hours=12),
            "question": "On Passage",
            "result": "Passed",
            "bill_id": bill.id,
            "source_url": "https://clerk.house.gov/Votes/202642",
            "totals": {"yea": 220, "nay": 210},
            "party_split": {"D": {"yea": 200}, "R": {"nay": 190}},
            "positions": [
                {
                    "bioguide_id": "R000037",
                    "name": "CA 37 Representative",
                    "state": "CA",
                    "party": "D",
                    "position": "yea",
                }
            ],
            "source_links": [
                {
                    "label": "House Clerk roll call",
                    "url": "https://clerk.house.gov/Votes/202642",
                    "source_system": "house.gov",
                    "retrieved_at": now,
                    "supports": ["vote result", "member positions"],
                }
            ],
        }
    )
    hearing = await legislative.upsert_hearing(
        {
            "event_id": "116500",
            "congress": 119,
            "chamber": "House",
            "title": "Oversight hearing on civic data access",
            "meeting_type": "Hearing",
            "status": "Scheduled",
            "scheduled_at": now + timedelta(days=2),
            "location": "Rayburn 2154",
            "committee": {
                "committee_code": "hsgo",
                "name": "House Oversight and Accountability",
                "chamber": "House",
                "jurisdiction": "Government operations oversight.",
                "congress_url": "https://www.congress.gov/committee/house-oversight-and-accountability/hsgo",
            },
            "source_url": "https://www.congress.gov/event/119th-congress/house-event/116500",
            "source_links": [
                {
                    "label": "Congress.gov hearing",
                    "url": "https://www.congress.gov/event/119th-congress/house-event/116500",
                    "source_system": "congress.gov",
                    "retrieved_at": now,
                    "supports": ["hearing schedule"],
                }
            ],
        }
    )
    await session.flush()

    await updates.create_update(
        _update(
            "generic-1",
            "Generic agency post",
            now,
            tags=["agency"],
            url="https://www.example.gov/generic",
        )
    )
    await updates.create_update(
        _update(
            "bill-action-1",
            "House passes Civic Data Transparency Act",
            now - timedelta(hours=18),
            tags=["bill", "lifecycle"],
            url="https://www.congress.gov/bill/119th-congress/house-bill/1234",
            bill_id=bill.id,
            bill_action_id=action.id if action else None,
            metadata={"event_type": "bill_action", "bill_canonical_id": bill.canonical_id},
        )
    )
    await updates.create_update(
        _update(
            "vote-1",
            "House records roll-call vote on civic data bill",
            now - timedelta(hours=12),
            tags=["vote"],
            url="https://clerk.house.gov/Votes/202642",
            bill_id=bill.id,
            vote_id=vote.id,
            metadata={"event_type": "vote", "bill_canonical_id": bill.canonical_id},
        )
    )
    await updates.create_update(
        _update(
            "hearing-1",
            "House Oversight schedules civic data access hearing",
            now - timedelta(hours=20),
            event_date=hearing.scheduled_at,
            tags=["hearing", "oversight"],
            url="https://www.congress.gov/event/119th-congress/house-event/116500",
            hearing_id=hearing.id,
            metadata={"event_type": "hearing", "topics": ["oversight"]},
        )
    )
    await session.commit()

    service = FeedService(session)
    items, total = await service.list_updates(
        FeedQueryParams(
            sort="today",
            followed_bills=bill.canonical_id,
            followed_topics="oversight",
            state="CA",
            district="37",
            limit=10,
        )
    )

    assert total == 4
    assert [item["card_type"] for item in items[:3]] == ["vote", "hearing", "bill"]
    assert items[0]["headline"] == "House records roll-call vote on civic data bill"
    assert items[0]["rank_context"]["factors"]["lifecycle_importance"] > 0
    assert items[0]["rank_context"]["factors"]["followed_object_relevance"] > 0
    assert items[0]["source_trail_status"] == "available"
    assert items[0]["detail"]["vote"]["local_representative_positions"][0]["member_name"] == "CA 37 Representative"
    assert items[1]["detail"]["hearing"]["unavailable"]["transcripts"] == "Official transcript is not published yet."
    assert items[2]["detail"]["bill"]["vote_eligible"] is True
    assert "personal position" in items[2]["detail"]["bill"]["user_position_prompt"]


def _update(
    external_id: str,
    headline: str,
    published_at: datetime,
    *,
    tags: list[str],
    url: str,
    event_date: datetime | None = None,
    bill_id: int | None = None,
    bill_action_id: int | None = None,
    vote_id: int | None = None,
    hearing_id: int | None = None,
    metadata: dict | None = None,
) -> GovernmentUpdateCreate:
    return GovernmentUpdateCreate(
        external_id=external_id,
        source="congress.gov",
        branch=BranchEnum.LEGISLATIVE,
        headline=headline,
        summary=f"Summary for {headline}",
        full_text=None,
        published_at=published_at,
        event_date=event_date,
        url=url,
        bill_id=bill_id,
        bill_action_id=bill_action_id,
        vote_id=vote_id,
        hearing_id=hearing_id,
        tags=tags,
        metadata=metadata or {},
    )
