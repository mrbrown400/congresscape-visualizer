from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.civic import DocumentVersion
from app.services.document_version_pipeline import DocumentVersionPipeline, SourceDocument


@pytest_asyncio.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


def test_storage_and_extraction_are_content_addressed(tmp_path: Path) -> None:
    pipeline = DocumentVersionPipeline(tmp_path)
    content = b"Title\fName | Amount\nProject | 10"

    digest, path = pipeline.store_bytes(content)
    second_digest, second_path = pipeline.store_bytes(content)
    extraction = pipeline.extract(content, "text/plain")

    assert digest == second_digest
    assert path == second_path
    assert path.read_bytes() == content
    assert extraction.status == "complete"
    assert len(extraction.pages) == 2
    assert extraction.pages[1]["tables"] == [["Name", "Amount"], ["Project", "10"]]


def test_unsupported_content_has_explicit_failure_state(tmp_path: Path) -> None:
    extraction = DocumentVersionPipeline(tmp_path).extract(b"%PDF", "application/pdf")

    assert extraction.status == "unsupported"
    assert extraction.error == "no_extractor_for:application/pdf"


@pytest.mark.asyncio
async def test_persist_creates_immutable_document_version(session: AsyncSession, tmp_path: Path) -> None:
    pipeline = DocumentVersionPipeline(tmp_path)
    source = SourceDocument(
        canonical_id="la.metro:document:4402",
        source_system="la.metro",
        source_native_id="AttachmentId:4402",
        source_url="https://boardagendas.metro.net/report/4402.pdf",
        content_type="text/plain",
        retrieved_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        revision_key="2",
    )

    version = await pipeline.persist(session, source, b"official text")
    await session.commit()
    loaded = await session.scalar(select(DocumentVersion).where(DocumentVersion.id == version.id))

    assert loaded is not None
    assert loaded.extraction_status == "complete"
    assert loaded.metadata_json["storage_path"].endswith(loaded.byte_hash)
    loaded.byte_hash = "changed"
    with pytest.raises(ValueError, match="immutable"):
        await session.commit()
