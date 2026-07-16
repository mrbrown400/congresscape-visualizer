"""Content-addressed document storage and deterministic lightweight extraction."""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.civic import DocumentVersion


@dataclass(frozen=True, slots=True)
class SourceDocument:
    canonical_id: str
    source_system: str
    source_native_id: str
    source_url: str
    content_type: str
    retrieved_at: datetime
    revision_key: str
    published_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DocumentExtraction:
    status: str
    pages: tuple[dict[str, Any], ...] = ()
    error: str | None = None


class DocumentVersionPipeline:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def store_bytes(self, content: bytes) -> tuple[str, Path]:
        digest = hashlib.sha256(content).hexdigest()
        destination = self.storage_root / digest[:2] / digest
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(content)
        return digest, destination

    def extract(self, content: bytes, content_type: str) -> DocumentExtraction:
        if content_type in {"text/plain", "text/csv", "text/html", "application/xhtml+xml"}:
            text = content.decode("utf-8", errors="replace")
            if content_type in {"text/html", "application/xhtml+xml"}:
                text = html.unescape(re.sub(r"<[^>]+>", " ", text))
            pages = tuple(
                {"page": page_number, "text": page_text.strip(), "tables": self._tables(page_text)}
                for page_number, page_text in enumerate(text.split("\f"), start=1)
            )
            return DocumentExtraction(status="complete", pages=pages)
        return DocumentExtraction(status="unsupported", error=f"no_extractor_for:{content_type}")

    @staticmethod
    def _tables(text: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in text.splitlines():
            if "|" in line:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if cells and all(cells):
                    rows.append(cells)
        return rows

    async def persist(self, session: AsyncSession, source: SourceDocument, content: bytes) -> DocumentVersion:
        digest, path = self.store_bytes(content)
        extraction = self.extract(content, source.content_type)
        version = DocumentVersion(
            canonical_id=source.canonical_id,
            source_system=source.source_system,
            source_native_id=source.source_native_id,
            source_url=source.source_url,
            content_type=source.content_type,
            published_at=source.published_at,
            retrieved_at=source.retrieved_at,
            byte_hash=digest,
            revision_key=source.revision_key,
            extraction_status=extraction.status,
            extraction_error=extraction.error,
            metadata_json={"storage_path": str(path), "pages": list(extraction.pages)},
        )
        session.add(version)
        await session.flush()
        return version
