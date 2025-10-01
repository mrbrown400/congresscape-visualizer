"""Feed-related endpoints."""
from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.schemas.update import FeedQueryParams, FeedResponse
from app.services.feed_service import FeedService, get_feed_service

router = APIRouter()


@router.get("/", response_model=FeedResponse)
async def list_feed(
    params: FeedQueryParams = Depends(),
    service: FeedService = Depends(get_feed_service),
) -> FeedResponse:
    """Return feed items filtered by query parameters."""

    items, total = await service.list_updates(params)
    return FeedResponse(items=items, total=total)
