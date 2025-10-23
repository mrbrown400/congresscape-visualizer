"""Endpoint returning the once-per-day briefing payload."""
from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_db
from app.schemas.summary import DailyBriefResponse
from app.services.daily_summary_service import DailySummaryService
from app.services.notification_service import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=DailyBriefResponse)
async def fetch_daily_brief(
    target_date: date | None = Query(default=None, description="ISO date to fetch, defaults to today"),
    session: AsyncSession = Depends(get_db),
) -> DailyBriefResponse:
    """Return a curated summary of the day's most important government updates."""

    service = DailySummaryService(session)
    return await service.build_brief(target_date)


@router.post("/notify", status_code=status.HTTP_202_ACCEPTED)
async def push_daily_brief(
    target_date: date | None = Query(default=None, description="ISO date to send, defaults to today"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Trigger push notifications for the requested daily briefing."""

    summary_service = DailySummaryService(session)
    brief = await summary_service.build_brief(target_date)

    notification_service = NotificationService(session)
    recipients = await notification_service.dispatch_daily_brief(brief)

    return {"summary_date": brief.summary_date, "recipients": recipients}
