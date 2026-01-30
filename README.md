# Congresscape Visualizer

Congresscape Visualizer is a full-stack platform that distills each day’s most important U.S. government activity into a single briefing. This repository contains the FastAPI backend, PostgreSQL schema, data ingestion modules, and React Native mobile client that powers the experience.

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
- **Unified Update Schema** – `government_updates` table captures id, timestamps, branch/source, headline, summary, full text, tags/entities, vector embedding, and metadata for future RAG experiences.
- **Modular Ingestion** – Source-specific modules for Congress (GPO, Congress.gov), Supreme Court (Juriscraper), and Executive sources (Federal Register, White House, agency `data.json`).
- **Summarization & Embeddings** – OpenAI-powered services produce snackable summaries and pgvector embeddings for personalization and semantic search.
- **Daily Briefing UX** – Mobile app opens to a narrative digest with quick highlights, deep-dive cards, and optional push notifications when a new briefing posts.

## Extensibility Roadmap
- Add Celery/Redis worker for scheduled ingestion and notifications.
- Implement vector similarity search and “Full Coverage” exploration endpoints.
- Expand entity graph using SAM.gov hierarchy & knowledge graph linking.
- Introduce user accounts, saved feeds, and notification preferences.
- Share component library with web via React Native Web.

## Accessibility & Design Guardrails
- High contrast color palette with branch-level accents.
- Large tap targets and VoiceOver-friendly copy.
- Expandable cards and future audio/video support for accessibility parity.

Refer to `docs/architecture.md` for system-level details and next-step considerations.
