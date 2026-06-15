# Current State Audit

Audit date: 2026-05-28.

## Branch Comparison

- Current branch: `claude/redesign-app-ui-3JUxK`, matching `origin/claude/redesign-app-ui-3JUxK`.
- `origin/main` is the canonical remote baseline. It is the `daily-summary` branch merged through `e02bb43`; `origin/daily-summary` and `origin/main` have the same tree.
- Local `main` is stale at `aebb380` and is behind `origin/main` by four commits.
- Current redesign branch is two commits ahead of `origin/main`. It adds Today-first navigation, saved/preferences contexts, Explore/You/detail/settings screens, and backend ingest/data-shape changes.
- `origin/claude/seating-charts-congress-bJY3N` forked from old `main` before the daily-summary merge. Its useful work is interactive House/Senate seating charts, but it should be rebased or merged onto `origin/main` before integration.

## Application State

- Backend exposes health, feed, ingest, summary, and notification routes under `/api/v1`.
- Frontend includes onboarding, Today, calendar, Explore, You, saved/settings/detail flows, API clients, saved-item context, and push registration.
- Backend can run locally with SQLite through `DATABASE_URL`; Docker still provides PostgreSQL with pgvector.
- Current model code is SQLite-compatible and comments out pgvector embedding persistence and vector indexes.

## High-Signal Risks

- Documentation still describes PostgreSQL/pgvector embeddings as active, while current model/update service code does not persist embeddings.
- `DATABASE_URL` is required at import time, so clean test and cloud environments need an explicit env var or `.env`.
- Ingest enrichment can compute embeddings, but `UpdateService` drops them in the current SQLite-compatible path.
- Frontend defines `npm run lint`, but ESLint is not installed in `frontend/package.json`.
- Expo SDK 50 dependencies are misaligned according to `npx expo install --check`.
- Frontend feed calls include sort values that backend query params ignore.
- `poetry run ruff check .` currently fails on existing app lint and untracked backend scripts.

## Verification Snapshot

- `cd backend && poetry run pytest`: passed, 1 test, with Pydantic v2 deprecation warnings.
- `cd backend && poetry run ruff check .`: failed with existing lint errors.
- `cd frontend && npx tsc --noEmit`: passed.
- `cd frontend && npm run lint`: failed because `eslint` is not installed.
- `npx expo install --check`: failed with Expo SDK 50 dependency mismatches.

## Browser Smoke Snapshot

- Backend local server started on `http://127.0.0.1:8000`.
- `GET /api/v1/health`: returned `{"status":"ok"}`.
- `GET /api/v1/summary/`: returned a populated briefing for `summary_date` `2026-05-28`.
- Expo web started on `http://localhost:8081` despite dependency mismatch warnings.
- Browser smoke navigated from onboarding to Today, Calendar, and Explore.
- Frontend successfully called `/api/v1/summary/`, calendar feed, and latest feed endpoints; backend returned 200 after FastAPI trailing-slash redirects where applicable.
- Today rendered `WEDNESDAY, MAY 27` while the API summary date was `2026-05-28`, so date/timezone handling should be reviewed.
- Browser console warnings: push notification permission not granted, deprecated `props.pointerEvents`.
- Browser console error: `Unexpected text node: . A text node cannot be a child of a <View>.`
- Browser screenshot capture timed out through the in-app Browser CDP path; DOM snapshots were used as verification evidence instead.

## Harness Migration Outcome

Congresscape now follows the VeloRail-style Codex-native pattern:

- Static root `AGENTS.md` as the Codex entrypoint.
- Focused repo-local skills under `.agents/skills/`.
- Static harness docs under `docs/agentic/`.
- Generated repo map via `npm run agent:repo-map`.
- Lightweight root quality scripts that call backend and frontend checks.
- No new harness daemon, MCP server, persistent index, memory database, or orchestration UI.
