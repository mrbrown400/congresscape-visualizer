"""Member and district lookup endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.ingest.congress import fetch_census_district_lookup
from app.models.legislative import CongressionalMember
from app.schemas.legislative import DistrictLookupResponse
from app.services.legislative_service import LegislativeDataService

router = APIRouter()


@router.get("/district-lookup", response_model=DistrictLookupResponse)
async def resolve_district_lookup(
    address: str | None = Query(default=None, min_length=3),
    zip_code: str | None = Query(default=None, min_length=5, max_length=10),
    session: AsyncSession = Depends(get_db),
) -> DistrictLookupResponse:
    """Resolve a user location to district, representative, and senators."""

    if not address and not zip_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="address or zip_code is required",
        )

    try:
        lookup_payload = await fetch_census_district_lookup(address=address, zip_code=zip_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    service = LegislativeDataService(session)
    lookup = await service.resolve_district_members(**lookup_payload)
    await session.commit()

    representative = None
    if lookup.representative_member_id:
        representative = await session.get(CongressionalMember, lookup.representative_member_id)

    senators: list[CongressionalMember] = []
    if lookup.senator_member_ids:
        result = await session.execute(
            select(CongressionalMember).where(CongressionalMember.id.in_(lookup.senator_member_ids))
        )
        senators = list(result.scalars().all())

    return DistrictLookupResponse(
        lookup_key=lookup.lookup_key,
        lookup_type=lookup.lookup_type,
        query=lookup.query,
        state=lookup.state,
        district=lookup.district,
        source=lookup.source,
        retrieved_at=lookup.retrieved_at,
        ambiguity_reason=lookup.ambiguity_reason,
        representative=representative,
        senators=senators,
    )
