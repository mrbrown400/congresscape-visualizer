"""Small durable controls for recurring ingestion and operator recovery."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.runtime import IngestionRun, ReviewQueueItem, RuntimeLock, SourceCheckpoint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def next_retry_at(now: datetime, attempt: int, *, base_seconds: int = 30, max_seconds: int = 3_600) -> datetime:
    return now.astimezone(timezone.utc) + timedelta(seconds=min(max_seconds, base_seconds * (2 ** max(attempt - 1, 0))))


class RuntimeReliabilityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def acquire_lock(self, lock_key: str, owner: str, *, now: datetime | None = None, ttl_seconds: int = 300) -> bool:
        current = (now or utcnow()).astimezone(timezone.utc)
        lock = await self.session.scalar(select(RuntimeLock).where(RuntimeLock.lock_key == lock_key))
        if lock is not None and _aware(lock.expires_at) > current and lock.owner != owner:
            return False
        if lock is None:
            lock = RuntimeLock(lock_key=lock_key, owner=owner, acquired_at=current, expires_at=current + timedelta(seconds=ttl_seconds))
            self.session.add(lock)
        else:
            lock.owner = owner
            lock.acquired_at = current
            lock.expires_at = current + timedelta(seconds=ttl_seconds)
        await self.session.commit()
        return True

    async def release_lock(self, lock_key: str, owner: str) -> bool:
        lock = await self.session.scalar(select(RuntimeLock).where(RuntimeLock.lock_key == lock_key, RuntimeLock.owner == owner))
        if lock is None:
            return False
        await self.session.delete(lock)
        await self.session.commit()
        return True

    async def start_run(self, run_key: str, source: str, *, checkpoint: dict[str, Any] | None = None, replay_of_id: int | None = None, now: datetime | None = None) -> IngestionRun:
        current = now or utcnow()
        existing = await self.session.scalar(select(IngestionRun).where(IngestionRun.run_key == run_key))
        if existing is not None:
            return existing
        run = IngestionRun(run_key=run_key, source=source, status="running", started_at=current, checkpoint=checkpoint or {}, replay_of_id=replay_of_id)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def finish_run(self, run_id: int, *, checkpoint: dict[str, Any] | None = None, now: datetime | None = None) -> IngestionRun:
        run = await self._run(run_id)
        run.status = "completed"
        run.finished_at = now or utcnow()
        if checkpoint is not None:
            run.checkpoint = checkpoint
        await self.session.commit()
        return run

    async def fail_run(self, run_id: int, error: str, *, now: datetime | None = None) -> IngestionRun:
        run = await self._run(run_id)
        run.status = "failed"
        run.error = error[:1000]
        run.finished_at = now or utcnow()
        run.attempt = (run.attempt or 0) + 1
        await self.session.commit()
        return run

    async def replay_run(self, run_id: int, *, now: datetime | None = None) -> IngestionRun:
        original = await self._run(run_id)
        replay_key = f"{original.run_key}:replay:{(now or utcnow()).isoformat()}"
        return await self.start_run(replay_key, original.source, checkpoint=original.checkpoint, replay_of_id=original.id, now=now)

    async def save_checkpoint(self, source: str, *, cursor: str | None, source_version: str | None, payload_hash: str | None, metadata: dict[str, Any] | None = None, now: datetime | None = None) -> SourceCheckpoint:
        checkpoint = await self.session.scalar(select(SourceCheckpoint).where(SourceCheckpoint.source == source))
        if checkpoint is None:
            checkpoint = SourceCheckpoint(source=source, cursor=cursor, source_version=source_version, payload_hash=payload_hash, observed_at=now or utcnow(), metadata_json=metadata or {})
            self.session.add(checkpoint)
        else:
            checkpoint.cursor = cursor
            checkpoint.source_version = source_version
            checkpoint.payload_hash = payload_hash
            checkpoint.observed_at = now or utcnow()
            checkpoint.metadata_json = metadata or {}
        await self.session.commit()
        await self.session.refresh(checkpoint)
        return checkpoint

    async def enqueue_review(self, source: str, reason: str, *, run_id: int | None = None, severity: str = "warning", payload: dict[str, Any] | None = None) -> ReviewQueueItem:
        item = ReviewQueueItem(source=source, reason=reason, run_id=run_id, severity=severity, payload=payload or {})
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def _run(self, run_id: int) -> IngestionRun:
        run = await self.session.get(IngestionRun, run_id)
        if run is None:
            raise ValueError(f"ingestion run {run_id} not found")
        return run


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
