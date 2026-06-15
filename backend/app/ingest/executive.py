"""Executive branch ingestion across multiple agency sources."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Congresscape/1.0; +http://localhost)"}
    async with httpx.AsyncClient(timeout=20, headers=headers) as client:
        try:
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
        except Exception:
            pass  # White House API sometimes blocks requests


async def fetch_federal_register_future_events() -> AsyncIterator[NormalizedUpdate]:
    """Fetch Federal Register documents with future effective dates or comment deadlines."""

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    fields = "fields%5B%5D=title&fields%5B%5D=document_number&fields%5B%5D=effective_on&fields%5B%5D=html_url&fields%5B%5D=abstract&fields%5B%5D=agencies&fields%5B%5D=comments_close_on&fields%5B%5D=publication_date"
    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch documents with future effective dates
        url = f"{FEDERAL_REGISTER_API}?per_page=25&{fields}&conditions%5Beffective_date%5D%5Bgte%5D={tomorrow}"
        response = await client.get(url)
        response.raise_for_status()
        for entry in response.json().get("results", []):
            effective_date = entry.get("effective_on")
            publication_date = entry.get("publication_date")
            if effective_date:
                yield NormalizedUpdate(
                    external_id=f"fr-effective-{entry.get('document_number', '')}",
                    source="federal_register",
                    branch="executive",
                    headline=f"Effective: {entry.get('title', 'Federal Register Document')}",
                    summary=f"Becomes effective on {effective_date}. {entry.get('abstract', '')[:200] if entry.get('abstract') else ''}",
                    full_text=entry.get("html_url", ""),
                    published_at=parse_date(publication_date) if publication_date else now,
                    event_date=parse_date(effective_date),
                    url=entry.get("html_url", ""),
                    tags=["effective-date", "upcoming"],
                    metadata={
                        "event_type": "effective_date",
                        "agencies": entry.get("agencies", []),
                        "document_number": entry.get("document_number"),
                    },
                )

        # Fetch documents with future comment deadlines
        comment_url = f"{FEDERAL_REGISTER_API}?per_page=25&{fields}&conditions%5Bcomment_date%5D%5Bgte%5D={tomorrow}"
        response2 = await client.get(comment_url)
        response2.raise_for_status()
        for entry in response2.json().get("results", []):
            comment_date = entry.get("comments_close_on")
            publication_date = entry.get("publication_date")
            if comment_date:
                yield NormalizedUpdate(
                    external_id=f"fr-comment-{entry.get('document_number', '')}",
                    source="federal_register",
                    branch="executive",
                    headline=f"Comment Deadline: {entry.get('title', 'Federal Register Document')}",
                    summary=f"Comments due by {comment_date}. {entry.get('abstract', '')[:200] if entry.get('abstract') else ''}",
                    full_text=entry.get("html_url", ""),
                    published_at=parse_date(publication_date) if publication_date else now,
                    event_date=parse_date(comment_date),
                    url=entry.get("html_url", ""),
                    tags=["comment-deadline", "upcoming"],
                    metadata={
                        "event_type": "comment_deadline",
                        "agencies": entry.get("agencies", []),
                        "document_number": entry.get("document_number"),
                    },
                )


async def fetch_scotus_calendar() -> AsyncIterator[NormalizedUpdate]:
    """Fetch Supreme Court oral arguments calendar."""

    # SCOTUS calendar page
    url = "https://www.supremecourt.gov/oral_arguments/argument_calendars.aspx"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

            # The SCOTUS website doesn't have a clean API, so we create a reference entry
            yield NormalizedUpdate(
                external_id=f"scotus-calendar-{datetime.now().strftime('%Y%m')}",
                source="supremecourt.gov",
                branch="judicial",
                headline="Supreme Court Oral Arguments Calendar",
                summary="Check supremecourt.gov for the current term's oral argument schedule",
                full_text=None,
                published_at=datetime.now(timezone.utc),
                url=url,
                tags=["oral-arguments", "scotus", "calendar"],
                metadata={"event_type": "calendar"},
            )

            # Also fetch orders list which shows upcoming order days
            orders_url = "https://www.supremecourt.gov/orders/ordersofthecourt.aspx"
            yield NormalizedUpdate(
                external_id=f"scotus-orders-{datetime.now().strftime('%Y%m')}",
                source="supremecourt.gov",
                branch="judicial",
                headline="Supreme Court Orders Calendar",
                summary="The Court typically releases orders on Mondays during the term",
                full_text=None,
                published_at=datetime.now(timezone.utc),
                url=orders_url,
                tags=["orders", "scotus", "calendar"],
                metadata={"event_type": "calendar"},
            )
        except Exception:
            pass
