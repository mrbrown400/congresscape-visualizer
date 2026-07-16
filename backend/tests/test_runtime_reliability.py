from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.models.runtime import SourceCheckpoint
from app.services.runtime_reliability import RuntimeReliabilityService, next_retry_at


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
async def test_locking_is_exclusive_until_expiration(session) -> None:
    service = RuntimeReliabilityService(session)
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)
    assert await service.acquire_lock("source:congress", "worker-a", now=now, ttl_seconds=60)
    assert not await service.acquire_lock("source:congress", "worker-b", now=now + timedelta(seconds=30))
    assert await service.acquire_lock("source:congress", "worker-b", now=now + timedelta(seconds=61))
    assert await service.release_lock("source:congress", "worker-b")


@pytest.mark.asyncio
async def test_runs_checkpoint_replay_and_review_queue_are_durable(session) -> None:
    service = RuntimeReliabilityService(session)
    run = await service.start_run("congress:2026-07-16", "congress", checkpoint={"cursor": "1"})
    await service.save_checkpoint("congress", cursor="2", source_version="119", payload_hash="hash")
    failed = await service.fail_run(run.id, "temporary source failure")
    replay = await service.replay_run(failed.id)
    review = await service.enqueue_review("congress", "source returned an unexpected schema", run_id=failed.id)
    assert failed.status == "failed"
    assert replay.replay_of_id == failed.id
    assert review.status == "open"
    checkpoint = await session.scalar(select(SourceCheckpoint).where(SourceCheckpoint.source == "congress"))
    assert checkpoint is not None
    assert checkpoint.cursor == "2"


def test_retry_backoff_is_bounded_and_monotonic() -> None:
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)
    assert next_retry_at(now, 1) == now + timedelta(seconds=30)
    assert next_retry_at(now, 3) == now + timedelta(seconds=120)
    assert next_retry_at(now, 20) == now + timedelta(seconds=3600)
