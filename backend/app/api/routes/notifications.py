"""Endpoints for registering device push tokens."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_db
from app.schemas.notification import PushTokenCreate, PushTokenRead
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
