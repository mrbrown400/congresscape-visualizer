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
    scraper.parse()

    # Juriscraper stores data as parallel arrays on the scraper object
    case_names = scraper.case_names or ()
    case_dates = scraper.case_dates or ()
    download_urls = scraper.download_urls or ()
    docket_numbers = scraper.docket_numbers or ()
    judges_list = scraper.judges or ()
    citations = scraper.citations or ()

    count = min(len(case_names), 10)
    for i in range(count):
        case_name = case_names[i] if i < len(case_names) else "Supreme Court Opinion"
        docket = docket_numbers[i] if i < len(docket_numbers) else "unknown"
        download_url = download_urls[i] if i < len(download_urls) else ""
        judges = judges_list[i] if i < len(judges_list) else ""
        citation = citations[i] if i < len(citations) else ""

        # Handle case_dates which can be a datetime.date object
        case_date = case_dates[i] if i < len(case_dates) else None
        if case_date:
            if hasattr(case_date, 'isoformat'):
                date_str = case_date.isoformat()
            else:
                date_str = str(case_date)
        else:
            date_str = datetime.now(timezone.utc).isoformat()

        yield NormalizedUpdate(
            external_id=f"scotus-{docket}",
            source="supremecourt.gov",
            branch="judicial",
            headline=str(case_name),
            summary=f"Supreme Court opinion. Judge: {judges}" if judges else "Supreme Court opinion",
            full_text=str(download_url) if download_url else "",
            published_at=parse_date(date_str),
            url=str(download_url) if download_url else "",
            tags=["scotus", "opinion"],
            metadata={"docket": docket, "judges": judges, "citation": citation},
        )
