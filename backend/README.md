# Congresscape Backend

FastAPI application that ingests, normalizes, and serves U.S. government updates across the Legislative, Judicial, and Executive branches. Built for extensibility with pgvector, LLM summarization, and modular ingestion workers.

## Features
- Async FastAPI service with PostgreSQL + pgvector storage
- Modular ingestion for Congress, Supreme Court, and Executive sources
- LLM-powered summarization and embeddings via OpenAI
- Daily summary API plus filtered feeds for deep dives
- Push notification service ready to fan out daily brief headlines via Expo
- Ready for personalization, vector search, and background workers

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
- `app/services` – daily summary builder, notification dispatch, feed + ingestion helpers
- `app/ingest` – pipelines for Congress, Courts, and Executive data
- `app/api` – FastAPI routers and dependencies
- `tests` – backend unit tests

## Next Steps
- Add background task runner (Celery or Arq) for scheduled ingest and automatic daily brief dispatch
- Implement pgvector similarity search endpoint
- Expand entity extraction and tag normalization
