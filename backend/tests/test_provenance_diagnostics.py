from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models as _models  # noqa: F401
from app.db.base import Base
from app.models.update import BranchEnum
from app.schemas.update import GovernmentUpdateCreate
from app.services.provenance_diagnostics import ProvenanceDiagnosticsService
from app.services.update_service import UpdateService


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_provenance_diagnostics_reports_fresh_stale_missing_and_failed_states(session) -> None:
    now = datetime(2026, 6, 16, 18, tzinfo=timezone.utc)
    updates = UpdateService(session)

    await updates.create_update(
        _update(
            "fresh",
            "Fresh sourced update",
            now,
            url="https://www.congress.gov/bill/119th-congress/house-bill/1",
            metadata={"source_fetched_at": now.isoformat()},
        )
    )
    await updates.create_update(
        _update(
            "stale",
            "Stale sourced update",
            now - timedelta(days=5),
            url="https://www.congress.gov/bill/119th-congress/house-bill/2",
            metadata={"source_fetched_at": (now - timedelta(days=4)).isoformat()},
        )
    )
    await updates.create_update(
        _update(
            "missing",
            "Missing source update",
            now - timedelta(hours=2),
            url=None,
            metadata={},
        )
    )
    await updates.create_update(
        _update(
            "failed",
            "Failed source update",
            now - timedelta(hours=3),
            url="https://api.congress.gov/v3/bill/119/hr/3",
            metadata={"source_failures": [{"message": "Congress.gov returned 503"}]},
        )
    )
    await session.commit()

    diagnostics = await ProvenanceDiagnosticsService(session).list_update_diagnostics(
        stale_after_hours=48,
        now=now,
    )

    by_external_id = {item.external_id: item for item in diagnostics.items}
    assert by_external_id["fresh"].freshness_status == "fresh"
    assert by_external_id["fresh"].source_url == "https://www.congress.gov/bill/119th-congress/house-bill/1"
    assert by_external_id["stale"].freshness_status == "stale"
    assert "older than 48 hours" in by_external_id["stale"].warnings[0]
    assert by_external_id["missing"].freshness_status == "missing_source"
    assert by_external_id["missing"].provenance_status == "missing"
    assert by_external_id["failed"].freshness_status == "failed"
    assert by_external_id["failed"].failures == ["Congress.gov returned 503"]
    assert diagnostics.counts == {"fresh": 1, "failed": 1, "missing_source": 1, "stale": 1}


def _update(
    external_id: str,
    headline: str,
    published_at: datetime,
    *,
    url: str | None,
    metadata: dict,
) -> GovernmentUpdateCreate:
    return GovernmentUpdateCreate(
        external_id=external_id,
        source="congress.gov",
        branch=BranchEnum.LEGISLATIVE,
        headline=headline,
        summary=f"Summary for {headline}",
        full_text=None,
        published_at=published_at,
        url=url,
        tags=["bill"],
        metadata=metadata,
    )
