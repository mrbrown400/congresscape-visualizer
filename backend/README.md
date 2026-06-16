# Congresscape Backend

FastAPI application for the Congresscape primary-source civic feed. It ingests, normalizes, and serves U.S. government activity with source trails, provenance, and additive civic-card contracts, starting with Congress.gov as the MVP backbone.

## Features
- Async FastAPI service with SQLAlchemy models and PostgreSQL/SQLite-compatible local workflows
- Congress.gov-first ingestion for bill, vote, hearing, committee, text, and member activity
- Additive civic-card schema for what happened, why it matters, involved entities, money context, and source trail
- Source/provenance fields and unavailable-state handling for factual claims
- Money-context contract that labels source relationships and does not infer corruption, motive, or intent
- Filtered feeds, daily summary compatibility, followed-object alert generation, personalization, vector search, and background workers
- Ingestion freshness/provenance diagnostics and deterministic civic-feed smoke seed data

## Getting Started

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

Create a `.env` based on `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/congresscape
OPENAI_API_KEY=sk-your-key
```

Initialize the database schema:

```bash
poetry run python -m app.db.init_db
```

Run tests:

```bash
poetry run pytest
```

## Project Structure

- `app/core` – configuration and settings
- `app/models` – SQLAlchemy models (pgvector enabled)
- `app/schemas` – Pydantic request/response models
- `app/services` – feed, summary, notification, ingestion, ranking, and enrichment helpers
- `app/ingest` – pipelines for Congress, Courts, and Executive data
- `app/api` – FastAPI routers and dependencies
- `tests` – backend unit tests

## Next Steps
- Add more Congress.gov lifecycle ingestion coverage into the canonical domain models
- Wire followed-object alert generation into the deployed push scheduler
- Expand deterministic smoke coverage as new feed/detail surfaces are added
