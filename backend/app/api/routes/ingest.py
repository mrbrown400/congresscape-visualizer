"""Endpoints for ingestion workflows."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import GovernmentUpdateCreate, GovernmentUpdateRead
from app.schemas.provenance import ProvenanceDiagnosticsResponse
from app.services.provenance_diagnostics import DEFAULT_STALE_AFTER_HOURS, ProvenanceDiagnosticsService
from app.services.update_service import UpdateService

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
