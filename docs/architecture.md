# Congresscape Visualizer Architecture

## Overview
Congresscape Visualizer is moving toward a primary-source civic feed: a Congress.gov-first product that packages government activity into sourced cards instead of political social media posts. The platform consists of a modular FastAPI backend, SQLAlchemy storage, ingestion pipelines, provenance-aware card contracts, and a React Native mobile client for Today, My Government, Bills, Votes, Hearings, Money, and Alerts.

## High-Level Components
- **SQLAlchemy Storage**: Stores current `government_updates` records and will expand to canonical bill, action, vote, hearing, member, committee, and source-link tables.
- **FastAPI Backend**: Provides REST APIs for ingesting, querying, filtering, and eventually serving canonical civic cards. Includes services for summarization, ranking, personalization, and provenance checks.
- **Civic Card Contract**: Defines shared backend/frontend fields for what happened, why it matters, involved entities, sourced money context, and source trails with unavailable-state handling.
- **Ingestion Workers**: Congress.gov API workers are the MVP backbone. Official page scraping is fallback only; executive and judicial workers remain future feed inputs rather than M0 blockers.
- **Money Context Adapters**: `backend/app/ingest/money.py` defines official-source boundaries for CBO, FEC/OpenFEC, LDA, USAspending, House/Senate disclosures, OGE, and appropriations links. `backend/app/services/money_context.py` labels direct, related-entity, topic, and unavailable context before feed cards render it.
- **React Native App**: Presents branch-aware feed surfaces and detail views that can show source trails, money context, and alert-worthy lifecycle changes. Built to share UI modules with a future web client.
- **Shared Utilities**: Feature flagging, analytics publishing, and background task orchestration prepared for future expansion.

## Data Flow
1. **Fetch**: Source-specific ingestion modules pull raw official data, starting with Congress.gov API endpoints for bills, actions, text, committees, hearings, votes, and members.
2. **Normalize**: Raw payloads map to `NormalizedUpdate` objects today and canonical civic domain records in future M1/M2 work.
3. **Preserve Provenance**: Source URLs, retrieval timestamps, source labels, and unavailable states travel with each factual claim.
4. **Enrich Carefully**: Summaries, rankings, and money context may explain relevance, but they must not invent facts or infer corruption, motive, or intent.
5. **Persist**: Data is saved through SQLAlchemy models, starting with `government_updates` and expanding to canonical civic tables.
6. **Serve**: FastAPI endpoints expose current feed/summary APIs and the additive civic card contract that future feed endpoints can adopt.
7. **Present**: React Native surfaces cards with what happened, why it matters, involved entities, money context, and source trail affordances.

## Provenance Requirements
- Every factual card claim needs source indexes into the card source trail or an explicit unavailable reason.
- Source trails should prefer official primary sources. Related supporting sources are allowed only when labeled by relationship.
- Money context must distinguish direct source matches, related entity matches, inferred topic/industry context, and unavailable data.
- Money copy must be neutral context, not an accusation or corruption signal.
- Source confidence labels travel with source-trail entries, while money relationship labels travel with each money-context row. UI surfaces must keep those labels visible near the source link or money fact.

## Modularity & Extensibility
- Backend service layers are split into API routes, schemas, services, and repositories (`db`).
- Ingestion uses a plug-in architecture: each source defines `fetch_updates()` and `map_to_update()` functions.
- Summarization provider interface allows swapping OpenAI with alternative LLMs.
- Vector search prepared with pgvector; service exposes a stub API to be implemented when needed.
- Mobile app uses feature-based structure (`features/dailyBrief`, `features/onboarding`, etc.) to scale to web and desktop clients.

## Deployment Considerations
- Containerized services (Dockerfile placeholders) ready for local dev with docker-compose.
- Background workers scheduled via Celery/Redis or serverless CRON depending on deployment target.
- Observability hooks for logging/metrics included via `structlog` and `OpenTelemetry` placeholders.

## Future Enhancements
- Real-time push for sourced alerts when bills move, representatives vote, hearings are scheduled, or text changes.
- Canonical district/member mapping and My Government surfaces.
- Money-source adapters for FEC/OpenFEC, LDA, USAspending, House/Senate disclosures, OGE, CBO, and appropriations context.
- Graph relationships between agencies and entities for explainable civic context.
- User account system with granular notification preferences.
- Vector-powered "Full Coverage" deep dives and conversational RAG exploration.
