"""Supreme Court ingestion via Free Law Project / Juriscraper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

try:
    from juriscraper.opinions.united_states.federal_appellate import scotus_slip as scotus_module
except ImportError:  # pragma: no cover - fallback for older package versions
    try:
        from juriscraper.opinions.united_states import scotus as scotus_module  # type: ignore[misc]
    except ImportError:  # pragma: no cover - optional dependency layout can change
        scotus_module = None  # type: ignore[assignment]

from app.ingest.base import NormalizedUpdate


def parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


async def fetch_supreme_court_updates() -> AsyncIterator[NormalizedUpdate]:
    """Yield recent Supreme Court opinions."""

    if scotus_module is None:
        raise RuntimeError(
            "Juriscraper SCOTUS scraper is unavailable. Ensure juriscraper exposes "
            "`juriscraper.opinions.united_states.federal_appellate.scotus_slip` (or legacy "
            "`juriscraper.opinions.united_states.scotus`)."
        )

    scraper = scotus_module.Site()
    opinions = scraper.parse()
    for opinion in opinions[:5]:
        docket = opinion.get("docket", "unknown")
        yield NormalizedUpdate(
            external_id=docket,
            source="freelawproject",
            branch="judicial",
            headline=opinion.get("case_name", "Supreme Court Opinion"),
            summary=opinion.get("summary", ""),
            full_text=opinion.get("download_url", ""),
            published_at=parse_date(opinion.get("date", datetime.now(timezone.utc).isoformat())),
            url=opinion.get("neutral_citation", ""),
            tags=opinion.get("nature_of_suit", []),
            metadata={"docket": docket, "judges": opinion.get("judge", [])},
        )
