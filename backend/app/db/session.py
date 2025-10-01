"""Database session and engine configuration."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Asyncpg DSN ends with +asyncpg to support asyncio stack.
engine = create_async_engine(settings.database_url, pool_pre_ping=True, echo=settings.debug)

async_session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    """FastAPI dependency that yields a transactional session."""

    async with async_session_factory() as session:
        yield session
