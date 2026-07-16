from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models
from app.db.base import Base
from app.schemas.claims import ClaimCorrectionCreate, ClaimCreate
from app.services.claim_service import ClaimService


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_claim_persists_source_location_and_support(session) -> None:
    document = models.DocumentVersion(
        canonical_id="metro:document:report-1:v1",
        source_system="metro",
        source_native_id="report-1",
        content_type="application/pdf",
        retrieved_at=datetime.now(timezone.utc),
        byte_hash="e" * 64,
        revision_key="v1",
    )
    session.add(document)
    await session.flush()
    claim = await ClaimService(session).create_claim(
        ClaimCreate(
            canonical_id="metro:claim:report-1:amount",
            source_system="metro",
            source_native_id="report-1:amount",
            document_version_id=document.id,
            subject="report-1",
            predicate="authorized_amount",
            value="1000000",
            claim_type="money",
            value_unit="USD",
            extraction_version="claims-1",
            extraction_method="fixture_parser",
            confidence="0.95",
            source_page=4,
            source_location="p4:table1:r2:c3",
            supporting_text="The board authorized $1,000,000.",
            table_cell="r2c3",
        )
    )
    await session.commit()

    loaded = await session.scalar(select(models.ExtractedClaim).where(models.ExtractedClaim.id == claim.id))
    assert loaded is not None
    assert loaded.source_page == 4
    assert loaded.supporting_text.startswith("The board")
    assert loaded.confidence == Decimal("0.95")


@pytest.mark.asyncio
async def test_claim_correction_appends_revision_without_mutating_fact(session) -> None:
    claim = await ClaimService(session).create_claim(
        ClaimCreate(
            canonical_id="metro:claim:1",
            subject="report-1",
            predicate="status",
            value="published",
            extraction_version="claims-1",
        )
    )
    revision = await ClaimService(session).add_correction(
        claim.id,
        ClaimCorrectionCreate(correction_reason="Source revision", corrected_value="adopted"),
    )
    await session.commit()

    assert revision.revision_number == 1
    loaded = await session.scalar(select(models.ExtractedClaim).where(models.ExtractedClaim.id == claim.id))
    assert loaded is not None
    assert loaded.value == "published"
    assert loaded.revisions[0].corrected_value == "adopted"
