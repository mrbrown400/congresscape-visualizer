"""Store Expo push tokens and deliver daily brief notifications."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationSubscription
from app.schemas.notification import PushTokenCreate
from app.schemas.summary import DailyBriefResponse


class NotificationService:
    """Persist device push tokens and fan out summary alerts via Expo."""

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_token(self, payload: PushTokenCreate) -> NotificationSubscription:
        subscription = NotificationSubscription(
            token=payload.token,
            platform=payload.platform,
            timezone=payload.timezone,
        )
        self.session.add(subscription)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            # Update existing row with the latest metadata instead.
            existing = await self._get_by_token(payload.token)
            if existing:
                existing.platform = payload.platform
                existing.timezone = payload.timezone
                self.session.add(existing)
                await self.session.commit()
                await self.session.refresh(existing)
                return existing
            raise
        await self.session.refresh(subscription)
        return subscription

    async def _get_by_token(self, token: str) -> NotificationSubscription | None:
        stmt = select(NotificationSubscription).where(NotificationSubscription.token == token)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def dispatch_daily_brief(self, brief: DailyBriefResponse) -> int:
        """Send a lightweight ping with today's headline to every registered device."""

        tokens = await self._all_tokens()
        if not tokens:
            return 0

        message = self._build_push_payload(tokens, brief)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.EXPO_PUSH_URL, json=message)
            response.raise_for_status()

        await self.session.execute(
            NotificationSubscription.__table__.update()
            .where(NotificationSubscription.token.in_(tokens))
            .values(last_notified_at=datetime.now(timezone.utc))
        )
        await self.session.commit()
        return len(tokens)

    async def _all_tokens(self) -> Sequence[str]:
        stmt = select(NotificationSubscription.token)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    def _build_push_payload(self, tokens: Iterable[str], brief: DailyBriefResponse) -> list[dict[str, str]]:
        title = brief.headline
        body = brief.narrative if len(brief.narrative) < 220 else brief.narrative[:217] + "..."

        return [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": {
                    "summary_date": brief.summary_date.isoformat(),
                    "headline": title,
                },
            }
            for token in tokens
        ]
