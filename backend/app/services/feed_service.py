"""Feed querying and personalization logic."""
from typing import List

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.update import GovernmentUpdate
from app.schemas.update import FeedQueryParams
from app.services.personalization import rank_updates


class FeedService:
    """High-level feed operations for API layer."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self) -> Select[tuple[GovernmentUpdate]]:
        return select(GovernmentUpdate).order_by(GovernmentUpdate.published_at.desc())

    def _apply_filters(self, query: Select, params: FeedQueryParams) -> Select:
        if params.branch:
            query = query.where(GovernmentUpdate.branch == params.branch)
        if params.source:
            query = query.where(GovernmentUpdate.source == params.source)
        if params.tag:
            query = query.where(GovernmentUpdate.tags.contains([params.tag]))
        if params.search:
            # Placeholder for vector search; fallback to case-insensitive headline match.
            pattern = f"%{params.search.lower()}%"
            query = query.where(func.lower(GovernmentUpdate.headline).like(pattern))
        return query

    async def list_updates(self, params: FeedQueryParams) -> tuple[List[GovernmentUpdate], int]:
        query = self._apply_filters(self._base_query(), params)

        total_stmt = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        result = await self.session.execute(query.offset(params.offset).limit(params.limit))
        items = rank_updates(result.scalars().all(), context={"params": params.model_dump(exclude_none=True)})
        return items, total
