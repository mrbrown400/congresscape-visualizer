from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.ingest.congress import (
    bill_lifecycle_payload_from_congress,
    district_lookup_payload_from_census,
    hearing_payload_from_congress,
    vote_payload_from_congress,
)
from app.models.legislative import (
    BillAction,
    BillTextVersion,
    CongressionalBill,
    CongressionalCommittee,
    CongressionalHearing,
    CongressionalVote,
    LegislativeSourceLink,
    MemberVotePosition,
)
from app.models.update import GovernmentUpdate
from app.schemas.update import GovernmentUpdateCreate
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
async def test_legislative_tables_register_with_db_init_path() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        table_names = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    await engine.dispose()

    assert {
        "congressional_bills",
        "bill_actions",
        "bill_text_versions",
        "congressional_committees",
        "congressional_votes",
        "member_vote_positions",
        "congressional_hearings",
        "district_lookup_results",
        "legislative_source_links",
    }.issubset(table_names)


@pytest.mark.asyncio
async def test_bill_lifecycle_upsert_is_idempotent(session) -> None:
    retrieved_at = datetime(2026, 6, 15, tzinfo=timezone.utc)
    payload = bill_lifecycle_payload_from_congress(
        {
            "bill": {
                "congress": 119,
                "type": "HR",
                "number": "1234",
                "title": "A bill to improve civic data access",
                "originChamber": "House",
                "introducedDate": "2026-06-01",
                "latestAction": {"actionDate": "2026-06-10", "text": "Referred to committee."},
                "policyArea": {"name": "Government Operations and Politics"},
                "url": "https://api.congress.gov/v3/bill/119/hr/1234",
                "committees": {
                    "committees": [
                        {
                            "systemCode": "hsgo",
                            "name": "House Oversight and Accountability",
                            "chamber": "House",
                        }
                    ]
                },
                "actions": {
                    "actions": [
                        {
                            "actionCode": "1000",
                            "actionDate": "2026-06-01",
                            "text": "Introduced in House",
                            "type": "IntroReferral",
                        }
                    ]
                },
                "textVersions": {
                    "textVersions": [
                        {
                            "type": "Introduced in House",
                            "date": "2026-06-01",
                            "formats": [
                                {"type": "Formatted XML", "url": "https://www.congress.gov/bill/119/hr/1234/text/xml"}
                            ],
                        }
                    ]
                },
                "summaries": {"summaries": [{"text": "Improves access."}]},
                "cosponsors": {"cosponsors": [{"bioguideId": "A000001"}]},
                "amendments": {"amendments": [{"number": "1"}]},
                "relatedBills": {"relatedBills": [{"number": "S.1234"}]},
                "subjects": {"legislativeSubjects": [{"name": "Transparency"}]},
                "cboCostEstimates": {"cboCostEstimates": [{"url": "https://www.cbo.gov/example"}]},
                "crsReports": {"crsReports": [{"url": "https://crsreports.congress.gov/example"}]},
            }
        },
        retrieved_at=retrieved_at,
    )

    service = LegislativeDataService(session)
    first = await service.upsert_bill(payload)
    second = await service.upsert_bill(payload | {"title": "Updated civic data access"})
    await session.commit()

    assert second.id == first.id
    assert second.title == "Updated civic data access"
    assert await _count(session, CongressionalBill) == 1
    assert await _count(session, BillAction) == 1
    assert await _count(session, BillTextVersion) == 1
    assert await _count(session, CongressionalCommittee) == 1
    assert await _count(session, LegislativeSourceLink) == 4


@pytest.mark.asyncio
async def test_source_link_preserves_confidence_category_and_supports(session) -> None:
    service = LegislativeDataService(session)

    source_link = await service.upsert_source_link(
        {
            "label": "LDA filing",
            "url": "https://lda.senate.gov/filings/public/filing/example",
            "source_system": "lda",
            "retrieved_at": datetime(2026, 6, 16, tzinfo=timezone.utc),
            "confidence": "topic_context",
            "source_category": "supporting",
            "supports": ["money_context", "lobbying_disclosure"],
        }
    )
    await session.commit()

    assert source_link.confidence == "topic_context"
    assert source_link.source_category == "supporting"
    assert source_link.supports == ["money_context", "lobbying_disclosure"]


@pytest.mark.asyncio
async def test_vote_upsert_links_known_members_and_preserves_unknown_members(session) -> None:
    service = LegislativeDataService(session)
    await service.upsert_member(
        {
            "bioguide_id": "K000001",
            "name": "Known Member",
            "party": "D",
            "state": "CA",
            "district": "37",
            "chamber": "House",
        }
    )
    vote_payload = vote_payload_from_congress(
        {
            "vote": {
                "chamber": "House",
                "congress": 119,
                "session": "2",
                "rollNumber": "42",
                "date": "2026-06-15",
                "question": "On Passage",
                "result": "Passed",
                "legislationType": "HR",
                "legislationNumber": "1234",
                "totals": {"yea": 220, "nay": 210},
                "partyTotals": {"D": {"yea": 200}, "R": {"nay": 200}},
                "url": "https://clerk.house.gov/Votes/202642",
                "members": [
                    {"bioguideId": "K000001", "name": "Known Member", "state": "CA", "party": "D", "voteCast": "Yea"},
                    {"memberId": "unknown-1", "name": "Unmatched Member", "state": "TX", "party": "R", "voteCast": "Nay"},
                ],
            }
        },
        retrieved_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )

    await service.upsert_vote(vote_payload)
    changed_payload = vote_payload | {
        "positions": [
            vote_payload["positions"][0] | {"position": "nay"},
            vote_payload["positions"][1],
        ]
    }
    await service.upsert_vote(changed_payload)
    await session.commit()

    assert await _count(session, CongressionalVote) == 1
    assert await _count(session, MemberVotePosition) == 2
    result = await session.execute(
        select(MemberVotePosition).where(MemberVotePosition.member_identifier == "K000001")
    )
    known_position = result.scalar_one()
    assert known_position.member_id is not None
    assert known_position.position == "nay"


@pytest.mark.asyncio
async def test_hearing_upsert_keeps_empty_media_and_witness_fallbacks(session) -> None:
    payload = hearing_payload_from_congress(
        {
            "committeeMeeting": {
                "eventId": "116500",
                "congress": 119,
                "chamber": "House",
                "title": "Oversight hearing",
                "date": "2026-06-20T14:00:00Z",
                "meetingStatus": "Scheduled",
                "type": "Hearing",
                "committees": [{"systemCode": "hsgo", "name": "House Oversight", "chamber": "House"}],
                "location": {"building": "Rayburn", "room": "2154"},
                "url": "https://www.congress.gov/event/119th-congress/house-event/116500",
            }
        },
        retrieved_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )

    service = LegislativeDataService(session)
    hearing = await service.upsert_hearing(payload)
    await service.upsert_hearing(payload | {"status": "Completed"})
    await session.commit()

    assert await _count(session, CongressionalHearing) == 1
    assert hearing.witnesses == []
    assert hearing.videos == []
    assert hearing.transcripts == []
    assert hearing.status == "Completed"
    assert hearing.location == "Rayburn 2154"


@pytest.mark.asyncio
async def test_district_lookup_resolves_90018_fixture_to_loaded_members(session) -> None:
    service = LegislativeDataService(session)
    rep = await service.upsert_member(
        {
            "bioguide_id": "R000037",
            "name": "CA 37 Representative",
            "party": "D",
            "state": "CA",
            "district": "37",
            "chamber": "House",
        }
    )
    senator_one = await service.upsert_member(
        {
            "bioguide_id": "S000001",
            "name": "California Senator One",
            "party": "D",
            "state": "CA",
            "chamber": "Senate",
        }
    )
    senator_two = await service.upsert_member(
        {
            "bioguide_id": "S000002",
            "name": "California Senator Two",
            "party": "D",
            "state": "CA",
            "chamber": "Senate",
        }
    )
    census_payload = district_lookup_payload_from_census(
        {
            "result": {
                "addressMatches": [
                    {
                        "geographies": {
                            "119th Congressional Districts": [
                                {"STUSAB": "CA", "CD119": "37", "BASENAME": "37"}
                            ]
                        }
                    }
                ]
            }
        },
        query="90018",
        lookup_type="zip",
        retrieved_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )

    lookup = await service.resolve_district_members(**census_payload)
    await session.commit()

    assert lookup.state == "CA"
    assert lookup.district == "37"
    assert lookup.representative_member_id == rep.id
    assert set(lookup.senator_member_ids) == {senator_one.id, senator_two.id}
    assert lookup.ambiguity_reason is None


@pytest.mark.asyncio
async def test_generic_update_can_reference_structured_bill_action(session) -> None:
    service = LegislativeDataService(session)
    bill = await service.upsert_bill(
        {
            "congress": 119,
            "bill_type": "hr",
            "number": "1234",
            "title": "Structured bill",
            "actions": [
                {
                    "canonical_id": "119-hr-1234:action:introduced",
                    "text": "Introduced in House",
                    "acted_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
                }
            ],
        }
    )
    action_result = await session.execute(select(BillAction))
    action = action_result.scalar_one()

    updater = UpdateService(session)
    update = await updater.upsert_update(
        GovernmentUpdateCreate(
            external_id="119-hr-1234:introduced",
            source="congress.gov",
            branch="legislative",
            headline="Structured bill introduced",
            summary="Introduced in House",
            full_text="",
            published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            url="https://www.congress.gov/bill/119th-congress/house-bill/1234",
            bill_id=bill.id,
            bill_action_id=action.id,
            tags=["bill", "action"],
            metadata={},
        )
    )
    await session.commit()

    assert await _count(session, GovernmentUpdate) == 1
    assert update.bill_id == bill.id
    assert update.bill_action_id == action.id


async def _count(session, model: type) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return result.scalar_one()
