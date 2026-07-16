"""Endpoints for ingestion workflows."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import GovernmentUpdateCreate, GovernmentUpdateRead
from app.schemas.runtime import RuntimeReviewCreate, RuntimeRunCreate, RuntimeRunRead, RuntimeRunUpdate
from app.models.runtime import IngestionRun, ReviewQueueItem
from app.schemas.provenance import ProvenanceDiagnosticsResponse
from app.services.provenance_diagnostics import DEFAULT_STALE_AFTER_HOURS, ProvenanceDiagnosticsService
from app.services.update_service import UpdateService
from app.services.runtime_reliability import RuntimeReliabilityService

router = APIRouter()


@router.post("/updates", response_model=GovernmentUpdateRead, status_code=status.HTTP_201_CREATED)
async def ingest_update(
    payload: GovernmentUpdateCreate,
    session: AsyncSession = Depends(get_db),
) -> GovernmentUpdateRead:
    """Ingest or update a government action."""

    updater = UpdateService(session)
    update = await updater.upsert_update(payload)
    await session.commit()
    await session.refresh(update)
    return update


@router.get("/diagnostics/provenance")
async def provenance_diagnostics(
    limit: int = 100,
    stale_after_hours: int = DEFAULT_STALE_AFTER_HOURS,
    session: AsyncSession = Depends(get_db),
) -> ProvenanceDiagnosticsResponse:
    """Return freshness and source-trail diagnostics for ingested feed records."""

    service = ProvenanceDiagnosticsService(session)
    return await service.list_update_diagnostics(limit=limit, stale_after_hours=stale_after_hours)


@router.post("/runs", response_model=RuntimeRunRead, status_code=status.HTTP_201_CREATED)
async def start_runtime_run(payload: RuntimeRunCreate, session: AsyncSession = Depends(get_db)) -> RuntimeRunRead:
    service = RuntimeReliabilityService(session)
    if payload.lock_key and payload.owner and not await service.acquire_lock(payload.lock_key, payload.owner):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ingestion lock is already held")
    run = await service.start_run(payload.run_key, payload.source, checkpoint=payload.checkpoint)
    return RuntimeRunRead.model_validate(run, from_attributes=True)


@router.post("/runs/{run_id}/complete", response_model=RuntimeRunRead)
async def complete_runtime_run(run_id: int, payload: RuntimeRunUpdate, session: AsyncSession = Depends(get_db)) -> RuntimeRunRead:
    try:
        run = await RuntimeReliabilityService(session).finish_run(run_id, checkpoint=payload.checkpoint)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RuntimeRunRead.model_validate(run, from_attributes=True)


@router.post("/runs/{run_id}/fail", response_model=RuntimeRunRead)
async def fail_runtime_run(run_id: int, payload: RuntimeRunUpdate, session: AsyncSession = Depends(get_db)) -> RuntimeRunRead:
    try:
        run = await RuntimeReliabilityService(session).fail_run(run_id, payload.error or "runtime run failed")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RuntimeRunRead.model_validate(run, from_attributes=True)


@router.post("/runs/{run_id}/replay", response_model=RuntimeRunRead, status_code=status.HTTP_201_CREATED)
async def replay_runtime_run(run_id: int, session: AsyncSession = Depends(get_db)) -> RuntimeRunRead:
    try:
        run = await RuntimeReliabilityService(session).replay_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RuntimeRunRead.model_validate(run, from_attributes=True)


@router.post("/review-queue", status_code=status.HTTP_201_CREATED)
async def enqueue_runtime_review(payload: RuntimeReviewCreate, session: AsyncSession = Depends(get_db)) -> dict[str, int]:
    item = await RuntimeReliabilityService(session).enqueue_review(
        payload.source, payload.reason, run_id=payload.run_id, severity=payload.severity, payload=payload.payload
    )
    return {"id": item.id}


@router.get("/runtime/diagnostics")
async def runtime_diagnostics(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    runs = list((await session.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(100))).scalars().all())
    review_count = await session.scalar(select(func.count()).select_from(ReviewQueueItem).where(ReviewQueueItem.status == "open"))
    counts: dict[str, int] = {}
    for run in runs:
        counts[run.status] = counts.get(run.status, 0) + 1
    return {"runs": counts, "recent_runs": len(runs), "open_review_items": int(review_count or 0)}
