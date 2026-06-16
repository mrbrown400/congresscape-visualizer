"""Congress (House/Senate) ingestion via GPO, Congress.gov, and unitedstates/congress."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.ingest.base import NormalizedUpdate
from app.services.legislative_service import canonical_bill_id, canonical_hearing_id, canonical_vote_id

US_GOVINFO_BILL_STATUS = "https://www.govinfo.gov/bulkdata/billstatus"
CONGRESS_GOV_API = "https://api.congress.gov/v3"
UNIFIED_CONGRESS_DATA = "https://unitedstates.github.io/congress-legislators/legislators-current.json"
CENSUS_GEOCODER_API = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"


def parse_date(value: str) -> datetime:
    sanitized = value.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(sanitized)
    except ValueError:
        try:
            return datetime.strptime(sanitized, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
                return datetime.now(timezone.utc)


def _parse_optional_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    parsed = parse_date(str(value))
    return parsed


def _as_list(value: Any, nested_key: str | None = None) -> list[dict]:
    if isinstance(value, dict) and nested_key:
        value = value.get(nested_key)
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _name_or_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("name") or value.get("value") or value.get("text")
    return value


def build_congress_bill_url(congress: int | str, bill_type: str, number: int | str) -> str:
    public_type = {
        "hr": "house-bill",
        "s": "senate-bill",
        "hjres": "house-joint-resolution",
        "sjres": "senate-joint-resolution",
        "hconres": "house-concurrent-resolution",
        "sconres": "senate-concurrent-resolution",
        "hres": "house-resolution",
        "sres": "senate-resolution",
    }.get(str(bill_type).lower(), str(bill_type).lower())
    return f"https://www.congress.gov/bill/{congress}th-congress/{public_type}/{number}"


def _source_link(
    *,
    label: str,
    url: str | None,
    retrieved_at: datetime,
    supports: list[str] | None = None,
    published_at: datetime | None = None,
    source_system: str = "congress.gov",
    confidence: str = "direct_source",
    source_category: str = "official",
) -> dict[str, Any] | None:
    if not url:
        return None
    return {
        "label": label,
        "url": url,
        "source_system": source_system,
        "retrieved_at": retrieved_at,
        "published_at": published_at,
        "confidence": confidence,
        "source_category": source_category,
        "supports": supports or [],
    }


def bill_lifecycle_payload_from_congress(
    payload: dict[str, Any],
    *,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    """Normalize a Congress.gov bill/detail payload for canonical persistence."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    bill = payload.get("bill", payload)
    congress = int(bill["congress"])
    bill_type = str(bill["type"]).lower()
    number = str(bill["number"])
    canonical_id = canonical_bill_id(congress, bill_type, number)
    latest_action = _as_dict(bill.get("latestAction"))
    congress_url = bill.get("congressUrl") or bill.get("congress_url") or build_congress_bill_url(
        congress, bill_type, number
    )

    source_links = [
        link
        for link in [
            _source_link(
                label="Congress.gov bill page",
                url=congress_url,
                retrieved_at=retrieved,
                supports=["bill"],
            ),
            _source_link(
                label="Congress.gov bill API",
                url=bill.get("url"),
                retrieved_at=retrieved,
                supports=["bill"],
            ),
        ]
        if link
    ]

    actions = []
    for index, action in enumerate(_as_list(bill.get("actions"), "actions")):
        acted_at = _parse_optional_date(action.get("actionDate") or action.get("acted_at"))
        action_url = action.get("url") or congress_url
        actions.append(
            {
                "canonical_id": f"{canonical_id}:action:{action.get('actionCode') or index}",
                "action_code": action.get("actionCode"),
                "action_type": _name_or_value(action.get("type")),
                "text": action.get("text") or "",
                "acted_at": acted_at,
                "chamber": action.get("chamber") or bill.get("originChamber"),
                "committee_code": action.get("committeeCode"),
                "source_url": action_url,
                "sequence": index,
                "metadata": {"raw": action},
                "source_links": [
                    link
                    for link in [
                        _source_link(
                            label="Congress.gov action source",
                            url=action_url,
                            retrieved_at=retrieved,
                            published_at=acted_at,
                            supports=["action"],
                        )
                    ]
                    if link
                ],
            }
        )

    if latest_action and not actions:
        acted_at = _parse_optional_date(latest_action.get("actionDate"))
        actions.append(
            {
                "canonical_id": f"{canonical_id}:action:latest",
                "text": latest_action.get("text") or "",
                "acted_at": acted_at,
                "chamber": bill.get("originChamber"),
                "source_url": congress_url,
                "sequence": 0,
                "metadata": {"raw": latest_action, "latest": True},
            }
        )

    text_versions = []
    for text_version in _as_list(bill.get("textVersions"), "textVersions"):
        version_code = text_version.get("type") or text_version.get("versionCode")
        source_url = text_version.get("url")
        formats = _as_list(text_version.get("formats"))
        if not source_url and formats:
            source_url = formats[0].get("url")
        text_versions.append(
            {
                "canonical_id": f"{canonical_id}:text:{version_code or len(text_versions)}",
                "version_code": version_code,
                "version_name": text_version.get("type") or text_version.get("name"),
                "published_at": _parse_optional_date(text_version.get("date")),
                "source_url": source_url,
                "formats": formats,
                "metadata": {"raw": text_version},
                "source_links": [
                    link
                    for link in [
                        _source_link(
                            label="Congress.gov bill text",
                            url=source_url,
                            retrieved_at=retrieved,
                            supports=["text"],
                        )
                    ]
                    if link
                ],
            }
        )

    committees = []
    for committee in _as_list(bill.get("committees"), "committees"):
        chamber = committee.get("chamber") or bill.get("originChamber")
        code = committee.get("systemCode") or committee.get("committeeCode") or committee.get("name")
        committees.append(
            {
                "committee_code": str(code).lower(),
                "name": committee.get("name") or str(code),
                "chamber": chamber,
                "committee_type": committee.get("type"),
                "congress_url": committee.get("url"),
                "metadata": {"raw": committee},
            }
        )

    return {
        "canonical_id": canonical_id,
        "congress": congress,
        "bill_type": bill_type,
        "number": number,
        "origin_chamber": bill.get("originChamber"),
        "title": bill.get("title") or bill.get("shortTitle") or f"{bill_type.upper()} {number}",
        "short_title": bill.get("shortTitle"),
        "introduced_at": _parse_optional_date(bill.get("introducedDate")),
        "latest_action_at": _parse_optional_date(latest_action.get("actionDate")),
        "latest_action_text": latest_action.get("text"),
        "policy_area": _name_or_value(bill.get("policyArea")),
        "congress_url": congress_url,
        "summaries": _as_list(bill.get("summaries"), "summaries"),
        "cosponsors": _as_list(bill.get("cosponsors"), "cosponsors"),
        "amendments": _as_list(bill.get("amendments"), "amendments"),
        "related_bills": _as_list(bill.get("relatedBills"), "relatedBills"),
        "subjects": _as_list(bill.get("subjects"), "legislativeSubjects"),
        "cbo_cost_estimates": _as_list(bill.get("cboCostEstimates"), "cboCostEstimates"),
        "crs_reports": _as_list(bill.get("crsReports"), "crsReports"),
        "committees": committees,
        "actions": actions,
        "text_versions": text_versions,
        "source_links": source_links,
        "metadata": {"raw": bill, "updateDate": bill.get("updateDate")},
    }


def vote_payload_from_congress(payload: dict[str, Any], *, retrieved_at: datetime | None = None) -> dict[str, Any]:
    """Normalize an official vote payload and member positions."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    vote = payload.get("houseRollCallVote") or payload.get("vote") or payload
    chamber = vote.get("chamber") or vote.get("voteChamber") or "House"
    congress = int(vote["congress"])
    session = str(vote.get("session")) if vote.get("session") is not None else None
    roll_number = str(vote.get("rollNumber") or vote.get("roll_number") or vote.get("voteNumber"))
    vote_date = _parse_optional_date(vote.get("date") or vote.get("voteDate"))

    bill_canonical_id = None
    bill = _as_dict(vote.get("bill") or vote.get("legislation"))
    bill_type = bill.get("type") or vote.get("legislationType")
    bill_number = bill.get("number") or vote.get("legislationNumber")
    if bill_type and bill_number:
        bill_canonical_id = canonical_bill_id(congress, str(bill_type).lower(), bill_number)

    members = _as_list(vote.get("members")) or _as_list(vote.get("positions"))
    positions = []
    for member in members:
        bioguide_id = member.get("bioguideId") or member.get("bioguide_id")
        identifier = bioguide_id or member.get("memberId") or member.get("id") or member.get("name")
        positions.append(
            {
                "member_identifier": identifier,
                "bioguide_id": bioguide_id,
                "name": member.get("name") or member.get("fullName") or str(identifier),
                "party": member.get("party"),
                "state": member.get("state"),
                "position": str(member.get("voteCast") or member.get("position") or "").lower() or "unknown",
                "metadata": {"raw": member},
            }
        )

    source_url = vote.get("sourceUrl") or vote.get("url")
    return {
        "canonical_id": canonical_vote_id(chamber, congress, session, roll_number),
        "chamber": chamber,
        "congress": congress,
        "session": session,
        "roll_number": roll_number,
        "vote_date": vote_date,
        "question": vote.get("question") or vote.get("description") or "",
        "result": vote.get("result"),
        "bill_canonical_id": bill_canonical_id,
        "source_url": source_url,
        "totals": _as_dict(vote.get("totals") or vote.get("voteTotals")),
        "party_split": _as_dict(vote.get("partyTotals") or vote.get("party_split")),
        "positions": positions,
        "source_links": [
            link
            for link in [
                _source_link(
                    label="Official roll-call vote",
                    url=source_url,
                    retrieved_at=retrieved,
                    published_at=vote_date,
                    supports=["vote", "member_positions"],
                )
            ]
            if link
        ],
        "metadata": {"raw": vote},
    }


def hearing_payload_from_congress(payload: dict[str, Any], *, retrieved_at: datetime | None = None) -> dict[str, Any]:
    """Normalize a Congress.gov committee meeting/hearing detail payload."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    meeting = payload.get("committeeMeeting") or payload.get("hearing") or payload
    event_id = str(meeting.get("eventId") or meeting.get("jacketNumber") or meeting.get("id"))
    chamber = meeting.get("chamber") or "Congress"
    congress = meeting.get("congress")
    scheduled_at = _parse_optional_date(meeting.get("date") or meeting.get("scheduledAt"))
    committees = _as_list(meeting.get("committees"))
    primary_committee = committees[0] if committees else {}
    location = meeting.get("location")
    if isinstance(location, dict):
        location = " ".join(str(part) for part in [location.get("building"), location.get("room")] if part).strip()

    videos = _as_list(meeting.get("videos"))
    transcripts = _as_list(meeting.get("transcripts"))
    source_url = meeting.get("sourceUrl") or meeting.get("url")
    if not source_url and congress:
        source_url = f"https://www.congress.gov/event/{congress}th-congress/{str(chamber).lower()}-event/{event_id}"

    source_links = [
        link
        for link in [
            _source_link(
                label="Congress.gov hearing or meeting source",
                url=source_url,
                retrieved_at=retrieved,
                published_at=scheduled_at,
                supports=["hearing"],
            ),
            *[
                _source_link(
                    label="Official hearing video",
                    url=video.get("url"),
                    retrieved_at=retrieved,
                    supports=["video"],
                )
                for video in videos
            ],
            *[
                _source_link(
                    label="Official hearing transcript",
                    url=transcript.get("url"),
                    retrieved_at=retrieved,
                    supports=["transcript"],
                )
                for transcript in transcripts
            ],
        ]
        if link
    ]

    return {
        "canonical_id": canonical_hearing_id(congress, chamber, event_id),
        "event_id": event_id,
        "congress": int(congress) if congress is not None else None,
        "chamber": chamber,
        "committee": {
            "committee_code": str(
                primary_committee.get("systemCode")
                or primary_committee.get("committeeCode")
                or primary_committee.get("name")
                or "unknown-committee"
            ).lower(),
            "name": primary_committee.get("name") or "Unknown committee",
            "chamber": primary_committee.get("chamber") or chamber,
            "committee_type": primary_committee.get("type"),
            "congress_url": primary_committee.get("url"),
            "metadata": {"raw": primary_committee},
        },
        "title": str(meeting.get("title") or "Committee meeting").replace("\r\n", " ").replace("\n", " ").strip(),
        "meeting_type": meeting.get("type"),
        "status": meeting.get("meetingStatus") or meeting.get("status"),
        "scheduled_at": scheduled_at,
        "location": location or None,
        "source_url": source_url,
        "witnesses": _as_list(meeting.get("witnesses")),
        "related_bills": _as_list(meeting.get("relatedBills") or meeting.get("relatedItems")),
        "videos": videos,
        "transcripts": transcripts,
        "source_links": source_links,
        "metadata": {
            "raw": meeting,
            "availability": {
                "witnesses": bool(_as_list(meeting.get("witnesses"))),
                "videos": bool(videos),
                "transcripts": bool(transcripts),
            },
        },
    }


def district_lookup_payload_from_census(
    payload: dict[str, Any],
    *,
    query: str,
    lookup_type: str,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    """Extract congressional district geography from a Census Geocoder response."""

    retrieved = retrieved_at or datetime.now(timezone.utc)
    matches = payload.get("result", {}).get("addressMatches", [])
    lookup_key = f"{lookup_type}:{query}".lower()
    if not matches:
        return {
            "lookup_key": lookup_key,
            "lookup_type": lookup_type,
            "query": query,
            "state": None,
            "district": None,
            "source": "census-geocoder",
            "retrieved_at": retrieved,
            "raw_response": payload,
            "ambiguity_reason": "Census Geocoder returned no address matches.",
        }

    if len(matches) > 1 and lookup_type == "zip":
        return {
            "lookup_key": lookup_key,
            "lookup_type": lookup_type,
            "query": query,
            "state": None,
            "district": None,
            "source": "census-geocoder",
            "retrieved_at": retrieved,
            "raw_response": payload,
            "ambiguity_reason": "ZIP code lookup returned multiple possible address geographies.",
        }

    geographies = matches[0].get("geographies", {})
    congressional_geo = None
    for name, values in geographies.items():
        if "Congressional District" in name and values:
            congressional_geo = values[0]
            break

    if not congressional_geo:
        return {
            "lookup_key": lookup_key,
            "lookup_type": lookup_type,
            "query": query,
            "state": None,
            "district": None,
            "source": "census-geocoder",
            "retrieved_at": retrieved,
            "raw_response": payload,
            "ambiguity_reason": "Census Geocoder response did not include congressional district geography.",
        }

    district = congressional_geo.get("CD119") or congressional_geo.get("CD118") or congressional_geo.get("CD") or congressional_geo.get("BASENAME")
    state = congressional_geo.get("STUSAB")
    if not state:
        states = _as_list(geographies.get("States"))
        if states:
            state = states[0].get("STUSAB") or states[0].get("STATE")
    if not state:
        state = congressional_geo.get("STATE")
    return {
        "lookup_key": lookup_key,
        "lookup_type": lookup_type,
        "query": query,
        "state": state,
        "district": str(district).zfill(2) if district not in (None, "") else None,
        "source": "census-geocoder",
        "retrieved_at": retrieved,
        "raw_response": payload,
        "ambiguity_reason": None,
    }


async def fetch_census_district_lookup(address: str | None = None, zip_code: str | None = None) -> dict[str, Any]:
    """Resolve an address or ZIP through Census Geocoder geography lookup."""

    query = address or zip_code
    if not query:
        raise ValueError("address or zip_code is required")

    params = {
        "address": query,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(CENSUS_GEOCODER_API, params=params)
        response.raise_for_status()
        return district_lookup_payload_from_census(
            response.json(),
            query=query,
            lookup_type="address" if address else "zip",
        )


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
                except Exception:
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
