# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Congresscape Visualizer is a full-stack platform for a primary-source civic feed: a Congress.gov-first way to follow government activity through sourced cards for Today, My Government, Bills, Votes, Hearings, Money, and Alerts. It consists of a FastAPI backend with SQLAlchemy storage and a React Native (Expo) mobile app.

## Common Commands

### Backend (from `/backend`)
```bash
poetry install                              # Install dependencies
poetry run uvicorn app.main:app --reload    # Run dev server (port 8000)
poetry run python -m app.db.init_db         # Initialize database schema
poetry run pytest                           # Run all tests
poetry run pytest tests/test_app.py -v      # Run specific test file
ruff check .                                # Lint code
```

### Frontend (from `/frontend`)
```bash
npm install                                 # Install dependencies
npm run start                               # Start Expo dev server
npm run ios                                 # Run on iOS simulator
npm run android                             # Run on Android emulator
npm run web                                 # Run in browser
npm run lint                                # ESLint check
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run start  # With custom API URL
```

### Docker (from root)
```bash
docker compose up -d db                     # Start PostgreSQL
```

## Architecture

### Backend (`/backend/app`)
- **Framework**: FastAPI with async SQLAlchemy 2.0
- **Database**: PostgreSQL (SQLite for local dev)
- **Entry point**: `main.py` creates FastAPI app, registers routes under `/api/v1`

**Key directories**:
- `api/routes/` - REST endpoints (feeds, ingest, summary, notifications, system)
- `models/` - SQLAlchemy ORM models (GovernmentUpdate, Entity, NotificationSubscription)
- `schemas/` - Pydantic request/response validation, including additive civic-card contracts
- `services/` - Business logic (daily_summary_service, feed_service, notification_service, ranking)
- `ingest/` - Data source connectors (congress.py, executive.py, judicial.py) with shared `NormalizedUpdate` dataclass
- `core/config.py` - Pydantic settings from environment variables
- `db/` - Database session management and initialization

**Data flow**: Ingest sources → NormalizedUpdate → Service layer → SQLAlchemy models → PostgreSQL

### Frontend (`/frontend/src`)
- **Framework**: React Native 0.73 with Expo 50
- **Language**: TypeScript (strict mode)
- **State management**: React Context + custom hooks (no Redux)

**Key directories**:
- `features/` - Feature modules (dailyBrief, calendar, feed, onboarding) each with screens/, hooks/, types
- `services/` - API client layer (fetch-based, talks to `/api/v1`)
- `navigation/` - React Navigation stack configuration
- `theme/` - Color palettes and ThemeProvider context

**Path aliases** configured in tsconfig: `@features/*`, `@services/*`, `@components/*`, `@theme/*`, etc.

### API Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/feed/` - List updates with filters (branch, source, tag, search, dates)
- `GET /api/v1/summary/` - Daily briefing for a date
- `POST /api/v1/ingest/updates` - Create/upsert government update
- `POST /api/v1/notifications/register` - Register Expo push token

## Key Patterns

- **Service layer pattern**: Business logic in `services/`, routes are thin wrappers
- **Async throughout**: All backend I/O uses async/await (asyncpg, httpx)
- **Modular ingestion**: Each data source (Congress, SCOTUS, Federal Register) implements fetch → normalize → persist
- **Source-backed claims**: Civic feed cards should include source trails, provenance, and unavailable states for factual claims
- **Money guardrail**: Money context must distinguish source relationship strength and must not infer corruption, motive, or intent
- **Feature-based frontend**: Each feature owns its screens, hooks, types, and components
- **Branch-aware styling**: UI uses color palette keyed by government branch (legislative, executive, judicial)

## Environment Variables

### Backend (`.env`)
- `DATABASE_URL` - PostgreSQL connection string
- `BACKEND_CORS_ORIGINS` - Allowed origins for CORS

### Frontend
- `EXPO_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000/api/v1)
