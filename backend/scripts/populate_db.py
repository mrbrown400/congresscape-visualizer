import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import get_session
from app.ingest.congress import fetch_house_and_senate_updates
from app.ingest.executive import fetch_federal_register_updates, fetch_white_house_actions, fetch_federal_register_future_events
from app.ingest.judicial import fetch_supreme_court_updates
from app.schemas.update import GovernmentUpdateCreate
from app.services.update_service import UpdateService
from app.models.update import BranchEnum

async def main():
    print("Starting ingestion...")
    async for session in get_session():
        service = UpdateService(session)

        # Congress
        print("Fetching Congress updates...")
        try:
            async for item in fetch_house_and_senate_updates():
                payload = GovernmentUpdateCreate(
                    external_id=item.external_id,
                    source=item.source,
                    branch=BranchEnum(item.branch),
                    headline=item.headline,
                    summary=item.summary,
                    full_text=item.full_text or None,
                    published_at=item.published_at,
                    event_date=item.event_date,
                    url=item.url if item.url else None,
                    tags=[t for t in item.tags if t],  # Filter out empty tags
                    metadata=item.metadata
                )
                await service.upsert_update(payload)
                print(f"  + Legislative: {item.headline[:60]}...")
        except Exception as e:
            print(f"Error fetching Congress updates: {e}")
            import traceback
            traceback.print_exc()

        # Executive
        print("Fetching Executive updates...")
        try:
            async for item in fetch_federal_register_updates():
                payload = GovernmentUpdateCreate(
                    external_id=item.external_id,
                    source=item.source,
                    branch=BranchEnum(item.branch),
                    headline=item.headline,
                    summary=item.summary,
                    full_text=item.full_text,
                    published_at=item.published_at,
                    event_date=item.event_date,
                    url=item.url,
                    tags=item.tags,
                    metadata=item.metadata
                )
                await service.upsert_update(payload)

            async for item in fetch_white_house_actions():
                payload = GovernmentUpdateCreate(
                    external_id=item.external_id,
                    source=item.source,
                    branch=BranchEnum(item.branch),
                    headline=item.headline,
                    summary=item.summary,
                    full_text=item.full_text,
                    published_at=item.published_at,
                    event_date=item.event_date,
                    url=item.url,
                    tags=item.tags,
                    metadata=item.metadata
                )
                await service.upsert_update(payload)
        except Exception as e:
            print(f"Error fetching Executive updates: {e}")

        # Future Events (effective dates, comment deadlines)
        print("Fetching Future Events...")
        try:
            async for item in fetch_federal_register_future_events():
                payload = GovernmentUpdateCreate(
                    external_id=item.external_id,
                    source=item.source,
                    branch=BranchEnum(item.branch),
                    headline=item.headline,
                    summary=item.summary,
                    full_text=item.full_text,
                    published_at=item.published_at,
                    event_date=item.event_date,
                    url=item.url,
                    tags=item.tags,
                    metadata=item.metadata
                )
                await service.upsert_update(payload)
        except Exception as e:
            print(f"Error fetching Future Events: {e}")

        # Judicial
        print("Fetching Judicial updates...")
        try:
            async for item in fetch_supreme_court_updates():
                payload = GovernmentUpdateCreate(
                    external_id=item.external_id,
                    source=item.source,
                    branch=BranchEnum(item.branch),
                    headline=item.headline,
                    summary=item.summary,
                    full_text=item.full_text or None,
                    published_at=item.published_at,
                    event_date=item.event_date,
                    url=item.url if item.url else None,
                    tags=[t for t in item.tags if t],
                    metadata=item.metadata
                )
                await service.upsert_update(payload)
                print(f"  + Judicial: {item.headline[:60]}...")
        except Exception as e:
            print(f"Error fetching Judicial updates: {e}")
            import traceback
            traceback.print_exc()

        await session.commit()
        print("Ingestion complete!")
        break

if __name__ == "__main__":
    asyncio.run(main())
