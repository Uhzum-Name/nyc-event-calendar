"""
Script to fetch NYC event data and generate an iCalendar (.ics) file.

This script is intended to be run as part of a scheduled job (e.g., GitHub
Actions) to produce an up‑to‑date calendar feed of free or interesting
art/music/culture events happening in New York City.  It uses the official
NYC Events Calendar API to query events by date range, category and
keywords, then writes them to a single `.ics` file.

Configuration
-------------
The script reads the following environment variables:

```
NYC_API_KEY   – your NYC API subscription key.  Required.
CATEGORIES    – comma‑separated list of category codes to include (e.g., "art,music").
BOROUGHS      – optional comma‑separated list of borough codes (Bk,Bx,Mn,Si,Qn,Ot).
DAYS_AHEAD    – optional integer number of days ahead to include (default=30).
```

You can set these variables in your CI/CD secrets or local environment.  When
no `BOROUGHS` are given the query includes all boroughs.

Note
----
The API only allows 10 results per request.  This script paginates through
results as needed.  See the API documentation at
https://api-portal.nyc.gov for details on available parameters【113356086683227†screenshot】.

"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests
from ics import Calendar, Event


API_BASE_URL = "https://api.nyc.gov/calendar/search"


def get_env_variable(name: str, default: str | None = None) -> str:
    """Fetch a variable from the environment or raise an exception if missing."""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name!r} must be set")
    return value


def parse_comma_separated(value: str | None) -> List[str]:
    """Split a comma‑separated string into a list of non‑empty values."""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def fetch_events(api_key: str,
                 start_date: datetime,
                 end_date: datetime,
                 categories: List[str],
                 boroughs: List[str],
                 keywords: str = "free",
                 max_pages: int = 5) -> List[Dict[str, Any]]:
    """Call the NYC Events Calendar API and return a list of event objects.

    The API returns at most 10 events per page.  This function loops
    over page numbers until no more results are returned or `max_pages`
    has been reached.
    """
    all_events: List[Dict[str, Any]] = []
    page_number = 1
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    while page_number <= max_pages:
        params = {
            "startDate": start_date.strftime("%m/%d/%Y %H:%M"),
            "endDate": end_date.strftime("%m/%d/%Y %H:%M"),
            "sort": "DATE",  # chronological order【699378210572664†screenshot】
            "keywords": keywords,
            "pageNumber": page_number,
        }
        if categories:
            params["categories"] = categories
        if boroughs:
            params["boroughs"] = boroughs

        try:
            resp = requests.get(API_BASE_URL, params=params, headers=headers)
        except Exception as exc:
            logging.error("Error contacting API: %s", exc)
            break

        if resp.status_code == 401:
            logging.error(
                "Access denied – check that your NYC_API_KEY is valid and that "
                "your API subscription is active."
            )
            break
        if resp.status_code != 200:
            logging.error("API responded with status %s: %s", resp.status_code, resp.text)
            break

        data = resp.json()
        events = data.get("events", [])
        if not events:
            break
        all_events.extend(events)
        # Stop if less than 10 records returned – no more pages.
        if len(events) < 10:
            break
        page_number += 1
    return all_events


def build_calendar(events: List[Dict[str, Any]], output_path: str) -> None:
    """Generate an iCalendar file from a list of event dictionaries."""
    cal = Calendar()
    for item in events:
        try:
            ev = Event()
            ev.name = item.get("name", "Unnamed Event")
            # Parse start and end times – expect ISO 8601 format from API
            start = item.get("startDate") or item.get("start")
            end = item.get("endDate") or item.get("end")
            if start:
                ev.begin = start
            if end:
                ev.end = end
            ev.location = item.get("location", "")
            ev.description = item.get("description", "")
            ev.extra["categories"] = ",".join(item.get("categories", []))
            cal.events.add(ev)
        except Exception as exc:
            logging.warning("Skipping event due to parsing error: %s", exc)
            continue
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cal)
    logging.info("Wrote %d events to %s", len(cal.events), output_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    api_key = get_env_variable("NYC_API_KEY")
    categories = parse_comma_separated(os.getenv("CATEGORIES"))
    boroughs = parse_comma_separated(os.getenv("BOROUGHS"))
    days_ahead = int(os.getenv("DAYS_AHEAD", "30"))

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days_ahead)

    logging.info(
        "Fetching events from %s through %s for categories %s and boroughs %s",
        start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"),
        categories if categories else "all", boroughs if boroughs else "all"
    )

    events = fetch_events(
        api_key=api_key,
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        boroughs=boroughs,
    )

    if not events:
        logging.warning("No events fetched – check your parameters or reduce filters.")

    output_file = os.path.join(os.path.dirname(__file__), "nyc_events.ics")
    build_calendar(events, output_file)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.error("Fatal error: %s", exc)
        sys.exit(1)