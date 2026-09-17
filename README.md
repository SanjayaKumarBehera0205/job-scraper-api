# Job Scraper API

A configurable job aggregation REST API built with FastAPI, asynchronous HTTP requests, Beautiful Soup, SQLAlchemy, JWT authentication, PostgreSQL, and Docker.

## Features

- User registration and JWT authentication
- Configurable career-page sources using CSS selectors
- Asynchronous HTML downloading with timeouts
- Job title, company, location, link, and description extraction
- Duplicate detection using stable URL hashes
- Refresh existing jobs and deactivate removed listings
- Keyword, company, location, and source filters
- Pagination and aggregate statistics
- Basic SSRF protection against private/local addresses
- SQLite for easy local development
- PostgreSQL and Docker deployment
- Automated parser and API tests

## How it works

1. Register and log in.
2. Add a public careers page as a source with its CSS selectors.
3. Call the source's scrape endpoint.
4. Search the stored, deduplicated jobs through the API.

## Run locally on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open Swagger UI: http://127.0.0.1:8000/docs

## Main endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Get JWT token |
| POST | `/api/v1/sources` | Configure a careers page |
| GET | `/api/v1/sources` | List sources |
| POST | `/api/v1/sources/{id}/scrape` | Fetch and parse one source |
| DELETE | `/api/v1/sources/{id}` | Delete a source and its jobs |
| GET | `/api/v1/jobs` | Search and filter jobs |
| GET | `/api/v1/jobs/{id}` | View one job |
| GET | `/api/v1/stats` | View aggregation statistics |

Login uses form data. Enter the email address in the `username` field.

## Example source configuration

```json
{
  "name": "Company Careers",
  "url": "https://company.example/careers",
  "job_selector": ".job-card",
  "title_selector": ".job-title",
  "company_selector": ".company",
  "location_selector": ".location",
  "link_selector": "a.job-link",
  "description_selector": ".summary"
}
```

CSS selectors differ between sites. Inspect the permitted public page and configure selectors that match its HTML.

## Run tests

```bash
pytest
```

## Docker with PostgreSQL

```bash
docker compose up --build
```

## Responsible use

Only scrape pages you are permitted to access. Review the website's terms and `robots.txt`, identify your client with a suitable user agent, use reasonable request rates, and prefer an official API when one is available. This project does not bypass authentication, CAPTCHAs, or access controls.

## Suggested improvements

- APScheduler or Celery for scheduled scraping
- Site-specific adapters for JSON-LD and ATS platforms
- Email alerts for matching jobs
- Alembic migrations
- Retry/backoff and per-domain rate limits
- CSV export
- GitHub Actions CI/CD

## License

MIT
