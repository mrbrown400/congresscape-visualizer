"""Check total government update count."""
# ruff: noqa: E402

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import get_session
from sqlalchemy import text

async def main():
    async for session in get_session():
        result = await session.execute(text("SELECT count(*) FROM government_updates"))
        count = result.scalar()
        print(f"Count: {count}")
        break

if __name__ == "__main__":
    asyncio.run(main())
