# Congresscape Visualizer Architecture

## Overview
Congresscape Visualizer distills each day’s government activity into a curated briefing covering the Legislative, Judicial, and Executive branches. The platform consists of a modular FastAPI backend with PostgreSQL + pgvector storage, an ingestion pipeline that normalizes diverse data sources, and a React Native mobile client focused on a single daily summary with optional push alerts.

## High-Level Components
- **PostgreSQL + pgvector**: Stores canonical `government_updates` records, embeddings, and metadata for personalization and future semantic search.
- **FastAPI Backend**: Provides REST APIs for ingesting, querying, filtering, and searching updates. Includes services for summarization (LLM), ranking, and personalization.
- **Ingestion Workers**: Modular fetchers for Congress, Courts, and Executive sources. Each worker normalizes data into a shared schema.
- **React Native App**: Presents the briefing as a narrative headline, highlight bullets, and deep-dive cards, with push notifications when a new summary drops. Built to share UI modules with a future web client.
- **Shared Utilities**: Feature flagging, analytics publishing, and background task orchestration prepared for future expansion.

## Data Flow
1. **Fetch**: Source-specific ingestion modules pull raw updates on a schedule (background tasks, Celery/Arq-ready).
2. **Normalize**: Raw payloads map to `NormalizedUpdate` objects with metadata (entities, tags, branch, source_url).
3. **Summarize & Embed**: LLM service generates snackable summaries; embeddings computed for the full text and stored in pgvector.
4. **Persist**: Data saved into PostgreSQL within `government_updates`, `entities`, and relation tables.
5. **Serve**: FastAPI endpoints expose the daily summary, feed lookups for deep dives, and notification registration; WebSocket/SSE remains ready for future real-time push.
6. **Present**: React Native app consumes the daily summary endpoint, rendering highlights and deep dives with branch-aware styling and optional notifications.

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
- Real-time WebSocket push for urgent alerts.
- Graph relationships between agencies (SAM.gov hierarchy) for network visualizations.
- User account system with granular notification preferences.
- Vector-powered "Full Coverage" deep dives and conversational RAG exploration.
