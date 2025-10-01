"""Congress (House/Senate) ingestion via GPO, Congress.gov, and unitedstates/congress."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from app.ingest.base import NormalizedUpdate

US_GOVINFO_BILL_STATUS = "https://www.govinfo.gov/bulkdata/billstatus"
CONGRESS_GOV_API = "https://api.congress.gov/v3"
UNIFIED_CONGRESS_DATA = "https://unitedstates.github.io/congress-legislators/legislators-current.json"


def parse_date(value: str) -> datetime:
    sanitized = value.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(sanitized)
    except ValueError:
        try:
            return datetime.strptime(sanitized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.now(timezone.utc)


async def fetch_house_and_senate_updates(api_key: str | None = None) -> AsyncIterator[NormalizedUpdate]:
    """Sample async generator that yields normalized updates for Congress."""

    params = {"api_key": api_key} if api_key else {}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{CONGRESS_GOV_API}/bill", params={"sort": "latest", **params})
        resp.raise_for_status()
        payload = resp.json()
        for item in payload.get("bills", [])[:5]:
            action = item.get("latestAction", {})
            published_at = action.get("actionDate") or item.get("updateDate") or datetime.now(timezone.utc).isoformat()
            yield NormalizedUpdate(
                external_id=item.get("number", "unknown"),
                source="congress.gov",
                branch="legislative",
                headline=item.get("title", ""),
                summary=item.get("summary", {}).get("text", ""),
                full_text=item.get("text", {}).get("url", ""),
                published_at=parse_date(published_at),
                url=item.get("congressdotgov_url", ""),
                tags=[item.get("policyArea", {}).get("name", "")] if item.get("policyArea") else [],
                metadata={"chamber": action.get("chamber"), "updateDate": item.get("updateDate")},
            )
