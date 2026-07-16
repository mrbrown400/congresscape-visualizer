from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models
from app.db.base import Base
from app.schemas.civic import GovernmentBodyCreate, JurisdictionCreate, MeetingCreate, PolicyActionCreate, PolicyItemCreate, PolicyItemRead
from app.services.civic_core_service import CivicCoreService


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_metro_item_body_meeting_action_round_trip(session) -> None:
    service = CivicCoreService(session)
    jurisdiction = await service.upsert_jurisdiction(
        JurisdictionCreate(canonical_id="la.metro", name="Metro", kind="service_area", source_system="metro", source_native_id="metro")
    )
    body = await service.upsert_government_body(
        GovernmentBodyCreate(
            canonical_id="la.metro:body:board", source_system="metro", source_native_id="board",
            jurisdiction_id=jurisdiction.id, name="Metro Board", body_type="board"
        )
    )
    item = await service.upsert_policy_item(
        PolicyItemCreate(
            canonical_id="la.metro:board-report:2026-0308", source_system="metro", source_native_id="report-2026-0308",
            jurisdiction_id=jurisdiction.id, item_type="board_report", title="Service plan"
        )
    )
    meeting = await service.upsert_meeting(
        MeetingCreate(
            canonical_id="la.metro:meeting:2026-03-08", source_system="metro", source_native_id="meeting-2026-03-08",
            government_body_id=body.id, meeting_type="board", scheduled_at=datetime(2026, 3, 8, tzinfo=timezone.utc)
        )
    )
    action = await service.upsert_policy_action(
        PolicyActionCreate(
            canonical_id="la.metro:board-report:2026-0308:action:1", source_system="metro", source_native_id="action-1",
            policy_item_id=item.id, actor_body_id=body.id, action_type="published", sequence=1
        )
    )
    await session.commit()

    loaded = await session.scalar(select(models.PolicyItem).where(models.PolicyItem.id == item.id))
    assert loaded is not None
    assert (loaded.jurisdiction.id, action.policy_item_id, meeting.government_body_id) == (jurisdiction.id, loaded.id, body.id)
    assert PolicyItemRead.model_validate(loaded).canonical_id == item.canonical_id


@pytest.mark.asyncio
async def test_upsert_uses_canonical_or_source_identity(session) -> None:
    service = CivicCoreService(session)
    first = await service.upsert_jurisdiction(
        JurisdictionCreate(canonical_id="la.metro", name="Metro", kind="service_area", source_system="metro", source_native_id="metro")
    )
    same_canonical = await service.upsert_jurisdiction(
        JurisdictionCreate(canonical_id="la.metro", name="Metro updated", kind="service_area", source_system="metro", source_native_id="metro")
    )
    same_source = await service.upsert_jurisdiction(
        JurisdictionCreate(canonical_id="la.metro:renamed", name="Metro latest", kind="service_area", source_system="metro", source_native_id="metro")
    )

    assert same_canonical.id == first.id
    assert same_source.id == first.id
    assert await session.scalar(select(func.count()).select_from(models.Jurisdiction)) == 1
    assert first.name == "Metro latest"
