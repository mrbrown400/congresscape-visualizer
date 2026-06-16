# Congresscape Visualizer

Congresscape Visualizer is a full-stack platform for a primary-source civic feed: a Congress.gov-first way to follow what changed in government without relying on political social media. This repository contains the FastAPI backend, PostgreSQL/SQLite-compatible schema, ingestion modules, and React Native mobile client that power sourced civic cards for Today, My Government, Bills, Votes, Hearings, Money, and Alerts.

## Repository Layout
- `backend/` – FastAPI app, PostgreSQL models (pgvector), ingestion services, and LLM summarization helpers.
- `frontend/` – React Native (Expo) mobile app with a TikTok-style feed UI.
- `docker-compose.yml` – Local stack for Postgres + backend service.
- `docs/` – Architectural overview.

## Quick Start
1. **Launch infrastructure**
   ```bash
   docker compose up -d db
   docker compose exec db psql -U postgres -d congresscape -c "CREATE EXTENSION IF NOT EXISTS vector"
   ```
   The `pgvector` extension must be enabled before initializing the schema. If you are using a local PostgreSQL instance instead of Docker, install the extension (via `CREATE EXTENSION vector;`) on the `congresscape` database manually.
2. **Backend**
   ```bash
   cd backend
   poetry install
   cp .env.example .env
   poetry run python -m app.db.init_db
   poetry run uvicorn app.main:app --reload
   ```
3. **Mobile App**
   ```bash
   cd frontend
   npm install
   EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run start
   ```
   Expo push notifications are now part of the workflow—configure your Expo project ID (via EAS or `app.json`) before testing device notifications.

## Key Features
- **Primary-Source Feed** – Congress.gov API is the first backbone for bill, vote, hearing, text, committee, and member activity; scraping official pages is fallback only.
- **Civic Card Contract** – Feed cards package what happened, why it matters, who is involved, money context, and source trail/provenance fields.
- **Sourced Money Context** – Money facts must be linked to official or supporting sources and must distinguish direct source matches from related entity or topic context. The product does not infer corruption, motive, or intent.
- **Modular Ingestion** – Congress.gov-first ingestion expands later to executive, judicial, disclosure, spending, and finance sources as feed inputs.
- **Alerts & Personal Context** – The app is shaped for alerts when bills move, representatives vote, hearings are scheduled, or official text changes.

## Extensibility Roadmap
- Add Celery/Redis worker for scheduled ingestion and notifications.
- Implement canonical bill, vote, hearing, member, district, and money-context domain models.
- Add source freshness/provenance checks before feed cards are ranked or alerted.
- Expand entity graph using official member, committee, disclosure, spending, and agency identifiers.
- Introduce user bill voting, followed objects, and representative comparison.
- Share component library with web via React Native Web.

## Accessibility & Design Guardrails
- High contrast color palette with branch-level accents.
- Large tap targets and VoiceOver-friendly copy.
- Expandable cards and future audio/video support for accessibility parity.

Refer to `docs/architecture.md` for system-level details and next-step considerations.
