# Congresscape Visualizer Architecture

The current shared-core migration decision is documented in [M6 Shared Civic Core Architecture Decision Record](m6-shared-civic-core.md). The companion [M6 database migration field map](m6-migration-field-map.md) and [schema rollout plan](m6-schema-rollout.md) define the additive generic domain, federal projection boundary, lifecycle semantics, provenance/version rules, compatibility contract, validation queries, and rollback sequence for CON-27 through CON-54.

## Overview
Congresscape Visualizer is moving toward a primary-source civic feed: a Congress.gov-first product that packages government activity into sourced cards instead of political social media posts. The platform consists of a modular FastAPI backend, SQLAlchemy storage, ingestion pipelines, provenance-aware card contracts, and a React Native mobile client for Today, My Government, Bills, Votes, Hearings, Money, and Alerts.

## High-Level Components
- **SQLAlchemy Storage**: Stores current `government_updates` records and will expand to canonical bill, action, vote, hearing, member, committee, and source-link tables.
- **FastAPI Backend**: Provides REST APIs for ingesting, querying, filtering, and serving civic-feed card data. Includes services for ranking, personalization, provenance diagnostics, and followed-object alert generation.
- **Civic Card Contract**: Defines shared backend/frontend fields for what happened, why it matters, involved entities, sourced money context, and source trails with unavailable-state handling.
- **Ingestion Workers**: Congress.gov API workers are the MVP backbone. Official page scraping is fallback only; executive and judicial workers remain future feed inputs rather than M0 blockers.
- **Money Context Adapters**: `backend/app/ingest/money.py` defines official-source boundaries for CBO, FEC/OpenFEC, LDA, USAspending, House/Senate disclosures, OGE, and appropriations links. `backend/app/services/money_context.py` labels direct, related-entity, topic, and unavailable context before feed cards render it.
- **React Native App**: Presents branch-aware feed surfaces, detail views, notification preferences, and My Government views that can show source trails, money context, and alert-worthy lifecycle changes. Built to share UI modules with a future web client.
- **Shared Utilities**: Feature flagging, analytics publishing, and background task orchestration prepared for future expansion.

## Data Flow
1. **Fetch**: Source-specific ingestion modules pull raw official data, starting with Congress.gov API endpoints for bills, actions, text, committees, hearings, votes, and members.
2. **Normalize**: Raw payloads map to `NormalizedUpdate` objects today and canonical civic domain records in future M1/M2 work.
3. **Preserve Provenance**: Source URLs, retrieval timestamps, source labels, and unavailable states travel with each factual claim.
4. **Enrich Carefully**: Summaries, rankings, and money context may explain relevance, but they must not invent facts or infer corruption, motive, or intent.
5. **Persist**: Data is saved through SQLAlchemy models, starting with `government_updates` and expanding to canonical civic tables.
6. **Diagnose**: Provenance diagnostics classify recent ingested updates as fresh, stale, missing-source, or failed so alert/feed reliability can be inspected.
7. **Serve**: FastAPI endpoints expose current feed/summary APIs, provenance diagnostics, followed-object alert candidates, and the additive civic card contract that future feed endpoints can adopt.
8. **Present**: React Native surfaces cards with what happened, why it matters, involved entities, money context, source trail affordances, and granular notification settings.

## Provenance Requirements
- Every factual card claim needs source indexes into the card source trail or an explicit unavailable reason.
- Source trails should prefer official primary sources. Related supporting sources are allowed only when labeled by relationship.
- Money context must distinguish direct source matches, related entity matches, inferred topic/industry context, and unavailable data.
- Money copy must be neutral context, not an accusation or corruption signal.
- Source confidence labels travel with source-trail entries, while money relationship labels travel with each money-context row. UI surfaces must keep those labels visible near the source link or money fact.
- Followed-object alerts must only publish candidates with a source URL, and money-context alerts require available, indexed source support.

## Modularity & Extensibility
- Backend service layers are split into API routes, schemas, services, and repositories (`db`).
- Ingestion uses a plug-in architecture: each source defines `fetch_updates()` and `map_to_update()` functions.
- Summaries arrive from source ingestion or submitted payloads; no paid LLM enrichment runs in the request path.
- Mobile app uses feature-based structure (`features/dailyBrief`, `features/onboarding`, etc.) to scale to web and desktop clients.

## Deployment Considerations
- Containerized services (Dockerfile placeholders) ready for local dev with docker-compose.
- Background workers scheduled via Celery/Redis or serverless CRON depending on deployment target.
- Observability hooks can be added when deployment needs them.

## Future Enhancements
- Production push scheduling for the source-backed followed-object alert candidates.
- Canonical district/member mapping and My Government surfaces.
- Money-source adapters for FEC/OpenFEC, LDA, USAspending, House/Senate disclosures, OGE, CBO, and appropriations context.
- Graph relationships between agencies and entities for explainable civic context.
- User account system for syncing granular notification preferences across devices.
