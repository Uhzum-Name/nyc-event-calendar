# NYC Events Calendar Feed

This repository contains a small utility for generating an automatically
updating iCalendar file (`nyc_events.ics`) with New York City events focused
on art, music and culture.  The calendar is populated using the City of
New York’s Events Calendar API, filtered by category and keywords.

## Contents

- `nyc_events_calendar.py` – Python script that queries the NYC Events
  Calendar API and writes an `.ics` file.  It expects configuration via
  environment variables (see below).
- `.github/workflows/update_calendar.yml` – GitHub Actions workflow that
  installs dependencies, runs the script daily, and commits any updates.
- `nyc_events.ics` – the generated calendar file (initially empty or
  containing sample data).

## Configuration

You need an API subscription key from the [NYC API Developers
Portal](https://api-portal.nyc.gov).  Once you have signed up and
subscribed to the **Events Calendar** API, add the key as a repository
secret named `NYC_API_KEY`.

Optional secrets:

- `CATEGORIES` – comma‑separated list of category codes to include.  Use
  the API’s `/categories` endpoint to discover valid codes.  Leave unset to
  include all categories.
- `BOROUGHS` – comma‑separated list of borough codes (Bk, Bx,
  Mn, Qn, Si, Ot)【717693515061609†screenshot】.
- `DAYS_AHEAD` – number of future days to include (default is 30).

Create these secrets in your repository **Settings → Secrets and variables**.

## How it works

1. The GitHub Actions workflow runs daily at approximately 5 AM
   New York time.  You can adjust the cron schedule in
   `.github/workflows/update_calendar.yml`.
2. It installs Python dependencies (`requests`, `ics`) and runs
   `nyc_events_calendar.py`, which queries events from the API with your
   categories, boroughs and time range filters【977620349214664†screenshot】.
3. The script writes the resulting events to `nyc_events.ics`.  If
   there are changes compared with the previous commit, the workflow
   commits and pushes the updated file.

### Subscribing in Apple Calendar

On a Mac, open Calendar and choose **File → New Calendar Subscription**【473308934250705†L411-L416】.  Paste the raw URL of your `nyc_events.ics` file (for example,
`https://raw.githubusercontent.com/username/nyc-events-calendar/main/nyc_events.ics`) and set the auto‑refresh interval (daily or hourly)【473308934250705†L432-L433】.  The calendar will update automatically whenever the workflow updates the file.

## Local testing

To run the script locally, create a virtual environment, install
dependencies (`pip install requests ics`), set the required environment
variables and run `python nyc_events_calendar.py`.  A file named
`nyc_events.ics` will be created in the repository root.

## License

This project is provided under the MIT License.