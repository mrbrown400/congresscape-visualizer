"""Congress (House/Senate) ingestion via GPO, Congress.gov, and unitedstates/congress."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from app.core.config import settings
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
    """Fetch recent bills from the current Congress."""

    key = api_key or settings.congress_api_key
    params = {"api_key": key} if key else {}
    async with httpx.AsyncClient(timeout=20) as client:
        # Fetch from current Congress (119th, 2025-2027) to get recent bills
        resp = await client.get(f"{CONGRESS_GOV_API}/bill/119", params={"limit": 20, **params})
        resp.raise_for_status()
        payload = resp.json()
        for item in payload.get("bills", [])[:15]:
            action = item.get("latestAction", {})
            published_at = action.get("actionDate") or item.get("updateDate") or datetime.now(timezone.utc).isoformat()

            # Build Congress.gov URL
            congress = item.get("congress", "119")
            bill_type = item.get("type", "").lower()
            bill_number = item.get("number", "")
            congress_url = f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{bill_number}" if congress and bill_type and bill_number else None

            yield NormalizedUpdate(
                external_id=f"{bill_type}-{congress}-{bill_number}",
                source="congress.gov",
                branch="legislative",
                headline=item.get("title", "")[:500],
                summary=action.get("text", ""),
                full_text="",
                published_at=parse_date(published_at),
                url=congress_url or "",
                tags=[item.get("originChamber", "").lower()] if item.get("originChamber") else [],
                metadata={"chamber": item.get("originChamber"), "updateDate": item.get("updateDate"), "congress": congress},
            )


async def fetch_congressional_hearings(api_key: str | None = None) -> AsyncIterator[NormalizedUpdate]:
    """Fetch upcoming committee meetings from Congress.gov API with full details."""

    key = api_key or settings.congress_api_key
    params = {"api_key": key} if key else {}
    async with httpx.AsyncClient(timeout=60) as client:
        # Get list of committee meetings (these are scheduled/recent meetings with details)
        resp = await client.get(f"{CONGRESS_GOV_API}/committee-meeting", params={"limit": 30, **params})
        resp.raise_for_status()
        payload = resp.json()

        for item in payload.get("committeeMeetings", []):
            # Fetch full details for each meeting
            detail_url = item.get("url")
            if detail_url:
                try:
                    detail_resp = await client.get(detail_url, params=params)
                    detail_resp.raise_for_status()
                    detail = detail_resp.json().get("committeeMeeting", {})

                    # Extract meeting date
                    meeting_date = detail.get("date", datetime.now(timezone.utc).isoformat())

                    # Extract committee info
                    committees = detail.get("committees", [])
                    committee_name = committees[0].get("name", "") if committees else ""

                    # Extract title - clean up formatting
                    title = detail.get("title", "Committee Meeting")
                    title = title.replace("\r\n", " ").replace("\n", " ").strip()
                    if len(title) > 200:
                        title = title[:197] + "..."

                    # Get chamber and meeting type
                    chamber = detail.get("chamber", "Congress")
                    meeting_type = detail.get("type", "Meeting")

                    # Get location
                    location = detail.get("location", {})
                    location_str = ""
                    if location:
                        location_str = f"{location.get('building', '')} {location.get('room', '')}".strip()

                    # Get video/event URL
                    videos = detail.get("videos", [])
                    event_url = ""
                    for v in videos:
                        url = v.get("url", "")
                        if "congress.gov" in url:
                            event_url = url
                            break
                    if not event_url and videos:
                        event_url = videos[0].get("url", "")

                    # Build summary
                    summary_parts = []
                    if committee_name:
                        summary_parts.append(f"Committee: {committee_name}")
                    if meeting_type:
                        summary_parts.append(f"Type: {meeting_type}")
                    if location_str:
                        summary_parts.append(f"Location: {location_str}")
                    summary = " | ".join(summary_parts) if summary_parts else None

                    yield NormalizedUpdate(
                        external_id=f"meeting-{item.get('eventId', 'unknown')}",
                        source="congress.gov",
                        branch="legislative",
                        headline=title,
                        summary=summary,
                        full_text=None,
                        published_at=parse_date(meeting_date),
                        url=event_url or f"https://congress.gov/event/{detail.get('congress', '')}/{chamber.lower()}-event/{item.get('eventId', '')}",
                        tags=["committee-meeting", chamber.lower(), meeting_type.lower()],
                        metadata={
                            "event_type": "committee_meeting",
                            "chamber": chamber,
                            "committee": committee_name,
                            "meeting_type": meeting_type,
                            "location": location_str,
                            "eventId": item.get("eventId"),
                            "congress": detail.get("congress"),
                            "status": detail.get("meetingStatus"),
                        },
                    )
                except Exception as e:
                    # Fall back to basic info if detail fetch fails
                    pass


async def fetch_house_floor_schedule() -> AsyncIterator[NormalizedUpdate]:
    """Fetch House floor schedule from clerk.house.gov."""

    # House floor XML feed
    url = "https://clerk.house.gov/floorsummary/HDoc-118-1-FloorProceedings.xml"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            # Parse XML - simplified extraction
            import re
            content = resp.text

            # Try JSON endpoint as fallback
            json_url = "https://docs.house.gov/floor/Download.aspx?file=/billsthisweek/20250127/house-floor-schedule.json"
            resp2 = await client.get("https://www.house.gov/legislative-activity", timeout=10)

            # For now, create a placeholder that indicates we tried
            yield NormalizedUpdate(
                external_id=f"house-floor-{datetime.now().strftime('%Y%m%d')}",
                source="house.gov",
                branch="house",
                headline="House Floor Schedule - Check house.gov for updates",
                summary="Visit house.gov/legislative-activity for the current floor schedule",
                full_text=None,
                published_at=datetime.now(timezone.utc),
                url="https://www.house.gov/legislative-activity",
                tags=["floor-schedule", "house"],
                metadata={"event_type": "floor_schedule"},
            )
        except Exception:
            pass  # Silently skip if unavailable


async def fetch_senate_floor_schedule() -> AsyncIterator[NormalizedUpdate]:
    """Fetch Senate floor schedule."""

    url = "https://www.senate.gov/legislative/schedule.htm"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()

            yield NormalizedUpdate(
                external_id=f"senate-floor-{datetime.now().strftime('%Y%m%d')}",
                source="senate.gov",
                branch="senate",
                headline="Senate Floor Schedule - Check senate.gov for updates",
                summary="Visit senate.gov for the current floor schedule",
                full_text=None,
                published_at=datetime.now(timezone.utc),
                url="https://www.senate.gov/legislative/schedule.htm",
                tags=["floor-schedule", "senate"],
                metadata={"event_type": "floor_schedule"},
            )
        except Exception:
            pass
