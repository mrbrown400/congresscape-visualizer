"""Endpoints for ingestion workflows."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.update import GovernmentUpdateCreate, GovernmentUpdateRead
from app.services.embedding import EmbeddingService, get_embedding_service
from app.schemas.provenance import ProvenanceDiagnosticsResponse
from app.services.provenance_diagnostics import DEFAULT_STALE_AFTER_HOURS, ProvenanceDiagnosticsService
from app.services.summarization import SummarizationService, get_summarization_service
from app.services.update_service import UpdateService

router = APIRouter()


@router.post("/updates", response_model=GovernmentUpdateRead, status_code=status.HTTP_201_CREATED)
async def ingest_update(
    payload: GovernmentUpdateCreate,
    session: AsyncSession = Depends(get_db),
    summarizer: SummarizationService = Depends(get_summarization_service),
    embedder: EmbeddingService = Depends(get_embedding_service),
) -> GovernmentUpdateRead:
    """Ingest or update a government action, enriching with summary & embeddings."""

    summary = payload.summary
    if not summary and payload.full_text:
        try:
            summary = await summarizer.summarize(payload.full_text)
        except RuntimeError as exc:  # Missing API key
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    embedding = payload.embedding
    if embedding is None and payload.full_text:
        try:
            embedding = await embedder.embed(payload.full_text)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    enriched_payload = payload.model_copy(update={"summary": summary, "embedding": embedding})
    updater = UpdateService(session)
    update = await updater.upsert_update(enriched_payload)
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
