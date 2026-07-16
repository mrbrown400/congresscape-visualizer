"""Endpoints for registering device push tokens."""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import delete

from app.api.deps import get_db
from app.models.notification import SavedFeedFilter
from app.schemas.notification import (
    FollowedAlertRequest,
    FollowedAlertResponse,
    PushTokenCreate,
    PushTokenRead,
    SavedFeedFilterCreate,
    SavedFeedFilterRead,
)
from app.services.notification_service import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register", response_model=PushTokenRead, status_code=status.HTTP_201_CREATED)
async def register_push_token(
    payload: PushTokenCreate,
    session: AsyncSession = Depends(get_db),
) -> PushTokenRead:
    """Persist an Expo push token so we can fan out daily summary notifications."""

    service = NotificationService(session)
    record = await service.register_token(payload)
    return PushTokenRead.model_validate(record, from_attributes=True)


@router.post("/followed-alerts", response_model=FollowedAlertResponse)
async def followed_alerts(
    payload: FollowedAlertRequest,
    session: AsyncSession = Depends(get_db),
) -> FollowedAlertResponse:
    """Generate source-backed alerts for followed bills, members, topics, and committees."""

    service = NotificationService(session)
    return await service.build_followed_alerts(payload)


@router.post("/filters", response_model=SavedFeedFilterRead, status_code=status.HTTP_201_CREATED)
async def save_filter(
    payload: SavedFeedFilterCreate,
    token: str = Query(..., min_length=10),
    session: AsyncSession = Depends(get_db),
) -> SavedFeedFilterRead:
    """Save a named query for one registered device."""

    record = await NotificationService(session).save_filter(token, payload.name, payload.filters)
    return SavedFeedFilterRead.model_validate(record, from_attributes=True)


@router.get("/filters", response_model=list[SavedFeedFilterRead])
async def list_filters(
    token: str = Query(..., min_length=10),
    session: AsyncSession = Depends(get_db),
) -> list[SavedFeedFilterRead]:
    records = await NotificationService(session).list_filters(token)
    return [SavedFeedFilterRead.model_validate(record, from_attributes=True) for record in records]


@router.delete("/filters/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    name: str,
    token: str = Query(..., min_length=10),
    session: AsyncSession = Depends(get_db),
) -> Response:
    await session.execute(delete(SavedFeedFilter).where(SavedFeedFilter.token == token, SavedFeedFilter.name == name))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
