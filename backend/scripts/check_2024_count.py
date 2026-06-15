import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import get_session

async def main():
    async for session in get_session():
        # Check count for 2024
        result = await session.execute(text("SELECT count(*) FROM government_updates WHERE published_at >= '2024-01-01' AND published_at < '2025-01-01'"))
        count = result.scalar()
        print(f"2024 Count: {count}")
        
        # Check total
        result_total = await session.execute(text("SELECT count(*) FROM government_updates"))
        print(f"Total Count: {result_total.scalar()}")
        break

if __name__ == "__main__":
    asyncio.run(main())
