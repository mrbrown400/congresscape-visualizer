# Congresscape Repo Map Lattice

This is the static relationship map for agent work. Use it with `docs/agentic/repo-map.md` when deciding owners, checks, and likely blast radius.

## Workstreams

| Workstream | Primary Files | Related Docs | Verification |
| --- | --- | --- | --- |
| Backend API | `backend/app/api/routes/`, `backend/app/schemas/`, `backend/app/services/` | `docs/architecture.md` | `cd backend && poetry run pytest`; `cd backend && poetry run ruff check .` |
| Database Models | `backend/app/models/`, `backend/app/db/` | `docs/architecture.md` | Schema init plus targeted service tests |
| Ingestion Data | `backend/app/ingest/`, `backend/app/services/ingest_pipeline.py`, `backend/app/services/update_service.py` | `docs/ingestion-sources.md` | Targeted ingest unit tests, network stubs, provenance checks |
| Primary-Source Civic Feed | `backend/app/schemas/civic_card.py`, `backend/app/services/feed_service.py`, `backend/app/api/routes/feeds.py`, `frontend/src/features/feed/`, `frontend/src/features/today/` | `docs/architecture.md`, `docs/ingestion-sources.md` | Backend schema tests, TypeScript, Expo web or Browser smoke |
| Notifications | `backend/app/api/routes/notifications.py`, `backend/app/services/notification_service.py`, `frontend/src/hooks/usePushNotifications.ts`, `frontend/src/features/settings/` | `docs/architecture.md` | Backend tests plus device/Expo caveat notes |
| Mobile UI | `frontend/src/features/`, `frontend/src/components/`, `frontend/src/navigation/`, `frontend/src/theme/` | `docs/agentic/current-state-audit.md` | `cd frontend && npx tsc --noEmit`; Browser/Expo web smoke when feasible |
| Harness | `AGENTS.md`, `.agents/skills/`, `docs/agentic/`, `scripts/build-repo-map.mjs`, `.codex/config.toml` | `docs/agentic/phase-1-codex-harness.md` | `npm run agent:repo-map`; docs review |

## Coupling Notes

- Backend response schemas and frontend TypeScript types must move together.
- `DATABASE_URL` is read at backend import time, so tests and cloud setup need an explicit database URL or `.env`.
- Summary and feed ranking currently share placeholder personalization logic; future feed ranking should preserve source transparency and avoid outrage-oriented engagement heuristics.
- Ingestion enrichment can compute summaries and embeddings, but current SQLite-compatible update models do not persist embeddings.
- Frontend path aliases must stay synchronized between `frontend/tsconfig.json` and `frontend/babel.config.js`.
- Browser-facing frontend changes should be checked through Expo web or an equivalent local browser smoke test when the dependency set can run.

## Branch Notes

- `origin/main` is the canonical remote baseline and already includes `daily-summary`.
- Local `main` is stale behind `origin/main`.
- Current `claude/redesign-app-ui-3JUxK` adds Today-first navigation, saved/preferences contexts, detail/settings screens, and ingest/data-shape changes.
- `origin/claude/seating-charts-congress-bJY3N` forked before the daily-summary merge; integrate it only after rebasing or merging onto `origin/main`.
