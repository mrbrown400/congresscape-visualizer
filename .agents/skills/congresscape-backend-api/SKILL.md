---
name: congresscape-backend-api
description: Use for FastAPI routes, Pydantic schemas, SQLAlchemy models, backend services, and backend tests.
---

# Congresscape Backend API

Use this skill for backend API and service work.

## Rules

- Keep routes thin and put business logic in `backend/app/services/`.
- Keep Pydantic schemas and frontend TypeScript types aligned when response shapes change.
- Be explicit about SQLite versus PostgreSQL/pgvector behavior.
- Avoid import-time surprises: `DATABASE_URL` is required when backend modules import settings.
- Do not compute OpenAI summaries or embeddings in tests unless explicitly mocked.

## Common Owners

- Routes: `backend/app/api/routes/`
- Schemas: `backend/app/schemas/`
- Models: `backend/app/models/`
- Services: `backend/app/services/`
- DB setup: `backend/app/db/`
- Tests: `backend/tests/`

## Verification

```bash
cd backend && poetry run pytest
cd backend && poetry run ruff check .
```

If Ruff fails on pre-existing issues, report the exact blockers and run targeted tests for the changed behavior.
