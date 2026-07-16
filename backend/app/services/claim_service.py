"""Persistence helpers for immutable source-backed claims."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.civic import ClaimRevision, ExtractedClaim
from app.schemas.claims import ClaimCorrectionCreate, ClaimCreate


class ClaimService:
    """Create immutable claims and append correction history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_claim(self, payload: ClaimCreate) -> ExtractedClaim:
        claim = ExtractedClaim(
            canonical_id=payload.canonical_id,
            source_system=payload.source_system,
            source_native_id=payload.source_native_id,
            source_url=payload.source_url,
            policy_item_id=payload.policy_item_id,
            document_version_id=payload.document_version_id,
            subject=payload.subject,
            predicate=payload.predicate,
            value=payload.value,
            claim_type=payload.claim_type,
            value_unit=payload.value_unit,
            value_date=payload.value_date,
            extraction_version=payload.extraction_version,
            extraction_method=payload.extraction_method,
            confidence=payload.confidence,
            source_page=payload.source_page,
            source_location=payload.source_location,
            supporting_text=payload.supporting_text,
            source_coordinates=payload.source_coordinates or {},
            table_cell=payload.table_cell,
            verified_at=payload.verified_at,
            review_state=payload.review_state,
            metadata_json=payload.metadata,
        )
        self.session.add(claim)
        await self.session.flush()
        return claim

    async def add_correction(self, claim_id: int, payload: ClaimCorrectionCreate) -> ClaimRevision:
        result = await self.session.execute(
            select(func.max(ClaimRevision.revision_number)).where(ClaimRevision.claim_id == claim_id)
        )
        latest = result.scalar_one_or_none() or 0
        revision = ClaimRevision(
            claim_id=claim_id,
            revision_number=latest + 1,
            correction_reason=payload.correction_reason,
            corrected_value=payload.corrected_value,
            corrected_supporting_text=payload.corrected_supporting_text,
            review_state=payload.review_state,
            verified_at=payload.verified_at,
            metadata_json=payload.metadata or {},
        )
        self.session.add(revision)
        await self.session.flush()
        return revision
