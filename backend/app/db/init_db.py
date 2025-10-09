"""Utility to initialize database schema."""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.db.base import Base
from app import models  # noqa: F401  # Ensure models are registered before table creation


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_models())
