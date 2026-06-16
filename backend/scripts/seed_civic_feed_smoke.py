"""Seed deterministic civic feed smoke data into the configured database."""
from __future__ import annotations

import asyncio

from app.db.session import async_session_factory
from app.services.civic_feed_smoke_seed import seed_civic_feed_smoke


async def main() -> None:
    async with async_session_factory() as session:
        result = await seed_civic_feed_smoke(session)
        print("Seeded civic feed smoke data")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
