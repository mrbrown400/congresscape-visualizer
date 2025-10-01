"""Executive branch ingestion across multiple agency sources."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from app.ingest.base import NormalizedUpdate

FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents"
WHITE_HOUSE_ACTIONS = "https://www.whitehouse.gov/wp-json/wp/v2/presidential-actions"
DATA_GOV_CATALOG = "https://api.data.gov"
SAM_GOV_HIERARCHY = "https://sam.gov/api/prod/sgs/v2/orgs"


def parse_date(value: str) -> datetime:
    sanitized = value.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(sanitized)
    except ValueError:
        try:
            return datetime.strptime(sanitized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)


async def fetch_federal_register_updates() -> AsyncIterator[NormalizedUpdate]:
    params = {"per_page": 5, "order": "desc", "sort": "newest"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(FEDERAL_REGISTER_API, params=params)
        response.raise_for_status()
        for entry in response.json().get("results", []):
            publication_date = entry.get("publication_date", datetime.now(timezone.utc).date().isoformat())
            yield NormalizedUpdate(
                external_id=str(entry.get("document_number", "")),
                source="federal_register",
                branch="executive",
                headline=entry.get("title", "Federal Register Document"),
                summary=entry.get("summary", ""),
                full_text=entry.get("html_url", ""),
                published_at=parse_date(publication_date),
                url=entry.get("html_url", ""),
                tags=[t.get("name") for t in entry.get("topics", []) if t.get("name")],
                metadata={"agencies": entry.get("agencies", [])},
            )


async def fetch_white_house_actions() -> AsyncIterator[NormalizedUpdate]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(WHITE_HOUSE_ACTIONS, params={"per_page": 5})
        response.raise_for_status()
        for entry in response.json():
            date_value = entry.get("date", datetime.now(timezone.utc).isoformat())
            tags = [term.get("name", "") for term in entry.get("terms", [])]
            yield NormalizedUpdate(
                external_id=str(entry.get("id", "")),
                source="whitehouse.gov",
                branch="executive",
                headline=entry.get("title", "White House Action"),
                summary=entry.get("excerpt", {}).get("rendered", ""),
                full_text=entry.get("content", {}).get("rendered", ""),
                published_at=parse_date(date_value),
                url=entry.get("link", ""),
                tags=[tag for tag in tags if tag],
                metadata={"slug": entry.get("slug")},
            )
