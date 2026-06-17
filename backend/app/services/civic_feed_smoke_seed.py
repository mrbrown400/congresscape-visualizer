"""Deterministic seed data for civic feed smoke checks."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legislative import BillAction
from app.models.update import BranchEnum
from app.schemas.update import GovernmentUpdateCreate
from app.services.legislative_service import LegislativeDataService
from app.services.update_service import UpdateService

SMOKE_NOW = datetime(2026, 6, 16, 18, tzinfo=timezone.utc)


async def seed_civic_feed_smoke(session: AsyncSession, *, now: datetime = SMOKE_NOW) -> dict[str, Any]:
    """Seed deterministic primary-source civic feed records for tests and local smoke."""

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
            "latest_action_at": now - timedelta(hours=5),
            "latest_action_text": "Passed House.",
            "policy_area": "Government Operations and Politics",
            "congress_url": "https://www.congress.gov/bill/119th-congress/house-bill/1234",
            "cosponsors": [{"name": "Example Cosponsor"}],
            "cbo_cost_estimates": [
                {
                    "title": "H.R. 1234 cost estimate",
                    "summary": "CBO estimates implementation would affect direct spending.",
                    "url": "https://www.cbo.gov/publication/12345",
                    "date": (now - timedelta(days=1)).isoformat(),
                }
            ],
            "actions": [
                {
                    "sequence": 1,
                    "action_type": "Passed House",
                    "text": "Passed/agreed to in House.",
                    "acted_at": now - timedelta(hours=5),
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
            "vote_date": now - timedelta(hours=2),
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
            "scheduled_at": now + timedelta(hours=18),
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
            "bill-action-1",
            "House passes Civic Data Transparency Act",
            now - timedelta(hours=5),
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
            "CA 37 Representative votes yea on civic data bill",
            now - timedelta(hours=2),
            tags=["vote"],
            url="https://clerk.house.gov/Votes/202642",
            bill_id=bill.id,
            vote_id=vote.id,
            metadata={
                "event_type": "vote",
                "bill_canonical_id": bill.canonical_id,
                "member_ids": ["R000037"],
                "members": [{"bioguide_id": "R000037", "state": "CA", "district": "37"}],
            },
        )
    )
    await updates.create_update(
        _update(
            "hearing-1",
            "House Oversight schedules civic data access hearing tomorrow",
            now - timedelta(hours=3),
            event_date=hearing.scheduled_at,
            tags=["hearing", "oversight"],
            url="https://www.congress.gov/event/119th-congress/house-event/116500",
            hearing_id=hearing.id,
            metadata={"event_type": "hearing", "topics": ["oversight"]},
        )
    )
    await updates.create_update(
        _update(
            "text-1",
            "New official text posted for Civic Data Transparency Act",
            now - timedelta(hours=4),
            tags=["bill", "text"],
            url="https://www.congress.gov/bill/119th-congress/house-bill/1234/text/ih",
            bill_id=bill.id,
            metadata={"event_type": "new_text", "bill_canonical_id": bill.canonical_id},
        )
    )
    await updates.create_update(
        _update(
            "money-1",
            "CBO posts direct cost estimate for Civic Data Transparency Act",
            now - timedelta(hours=1),
            tags=["money", "cbo"],
            url="https://www.cbo.gov/publication/12345",
            bill_id=bill.id,
            metadata={
                "card_type": "money",
                "bill_canonical_id": bill.canonical_id,
                "money_context": [
                    {
                        "label": "CBO cost estimate",
                        "value": "CBO published a direct cost estimate for this bill.",
                        "source_relationship": "direct_source",
                        "source_system": "cbo",
                        "source_url": "https://www.cbo.gov/publication/12345",
                        "supports": ["money_context", "cbo_cost_estimate"],
                    }
                ],
            },
        )
    )
    await session.commit()

    return {
        "bill_canonical_id": bill.canonical_id,
        "member_id": "R000037",
        "committee_id": "hsgo",
        "topic": "oversight",
        "source_urls": {
            "bill": "https://www.congress.gov/bill/119th-congress/house-bill/1234",
            "vote": "https://clerk.house.gov/Votes/202642",
            "hearing": "https://www.congress.gov/event/119th-congress/house-event/116500",
            "text": "https://www.congress.gov/bill/119th-congress/house-bill/1234/text/ih",
            "money": "https://www.cbo.gov/publication/12345",
        },
    }


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
