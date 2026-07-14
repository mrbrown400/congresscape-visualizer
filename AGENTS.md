# Agent Instructions

Congresscape Visualizer uses Codex as the active agent workflow. Keep durable project guidance in this repository through `AGENTS.md`, focused repo-local skills, `docs/agentic/`, and architecture docs. Do not depend on agent-private memory as the only source for repo behavior.

`CLAUDE.md` remains tracked for Claude-oriented compatibility. Codex should treat this file as the primary entrypoint.

## Project Mission

Congresscape Visualizer is a full-stack platform for a primary-source civic feed: a Congress.gov-first replacement for political social media that packages government activity into sourced cards with provenance, money context, and user bill voting. It consists of a FastAPI backend, SQLAlchemy data models, ingestion connectors, summary/notification services, and a React Native (Expo) mobile app.

Core product goals:
- Today, My Government, Bills, Votes, Hearings, Money, and Alerts surfaces that are useful at a glance.
- Congress.gov API as the primary backbone for the first MVP, with page scraping only as fallback.
- Source trails and provenance for factual claims, including clear unavailable states when official data has not appeared.
- Sourced money context that distinguishes direct facts from related context and never infers corruption, motive, or intent.
- Executive and judicial sources as future feed inputs, not blockers for the Congress.gov-first MVP.
- Push-ready notification workflows for source-backed alerts and important updates.

## Active Workflow

Prefer an issue-shaped frame for implementation, review, research, and automation work:
- Goal: the change, question, or decision being handled.
- Context: relevant files, docs, errors, screenshots, or prior decisions.
- Constraints: architecture, safety, scope, style, runtime, and tool limits.
- Done when: the verification, artifact, decision, or handoff that completes the task.

Use GitHub branches and PRs for code review when the task asks for publishable work. Include the issue key in branch names, commits, and PR descriptions when one exists.

Use Codex subagents for independent read-heavy audit, review, test triage, or disjoint implementation slices when the scope is clear. Keep write-heavy parallel work in disjoint files or modules, and have the main thread integrate and verify results.

## Repo-Local Skills

Repo-local Codex skills live in `.agents/skills/`. Read the matching skill before work:

- `.agents/skills/congresscape-task-runner/SKILL.md` for normal implementation tasks.
- `.agents/skills/congresscape-planning/SKILL.md` for task plans, migration plans, and architecture decisions.
- `.agents/skills/congresscape-backend-api/SKILL.md` for FastAPI routes, schemas, services, DB models, and tests.
- `.agents/skills/congresscape-ingest-data/SKILL.md` for Congress, executive, judicial, summary, and data provenance work.
- `.agents/skills/congresscape-frontend-mobile/SKILL.md` for Expo/React Native screens, navigation, theme, and mobile UX.
- `.agents/skills/congresscape-browser-verification/SKILL.md` for Expo web or browser-facing verification.
- `.agents/skills/congresscape-release-closeout/SKILL.md` for final verification and handoff.
- `.agents/skills/congresscape-harness-curation/SKILL.md` before adding or evaluating new skills, MCP servers, code indexers, memory stores, or orchestration tools.

## Harness Curation

Congresscape's agentic harness is intentionally small and static:
- `AGENTS.md` for repo entry instructions.
- `.agents/skills/` for repeatable Codex workflows.
- `docs/agentic/` for repo-local agent workflow knowledge.
- `docs/architecture.md` and domain docs for durable system decisions.
- GitHub for branches, commits, pull requests, and review.
- Direct backend/frontend quality commands for verification.

Approved reference posture:
- Use `github/spec-kit` only as a reference for issue specs, acceptance criteria, and implementation-plan shape.
- Use the Agent Skills structure as the format for repo-local `SKILL.md` files.
- Use external skill catalogs only to discover individual skills for review.
- Use Superpowers selectively when the installed workflow skill fits the task.
- Consider code maps as checked-in Markdown first, not as a daemon, database, or MCP server.

Do not add a new agentic harness daemon, MCP server, persistent index, memory database, orchestration UI, or broad hook layer by default. New harness runtimes must be evaluated outside this repo first and adopted only after a benchmark proves value without hiding source evidence.

## Quick Reference

```bash
npm run agent:repo-map
npm run quality
```

Backend commands from `backend/`:

```bash
poetry install
poetry run python -m app.db.init_db
poetry run uvicorn app.main:app --reload
poetry run pytest
poetry run pytest tests/test_app.py -v
poetry run ruff check .
```

Frontend commands from `frontend/`:

```bash
npm install
npm run start
npm run web
npm run ios
npm run android
npm run lint
npx tsc --noEmit
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run web
```

Docker commands from the repository root:

```bash
docker compose up -d db
```

## Architecture

### Backend (`backend/app`)

- Framework: FastAPI with async SQLAlchemy 2.0.
- Runtime database: configured by `DATABASE_URL`; current local `.env` can use SQLite, while Docker provides PostgreSQL.
- Entry point: `main.py` creates the app and registers routes under `/api/v1`.
- API routes: `api/routes/` owns feed, ingest, summary, notification, and system endpoints.
- Models: `models/` owns `GovernmentUpdate`, `Entity`, and notification subscriptions.
- Schemas: `schemas/` owns Pydantic request and response contracts.
- Services: `services/` owns feed, update, daily summary, notification, and ranking logic.
- Ingestion: `ingest/` owns Congress, executive, judicial, and runner modules using shared `NormalizedUpdate`.

### Frontend (`frontend/src`)

- Framework: React Native 0.73 with Expo 50.
- Language: TypeScript in strict mode.
- State: React Context and custom hooks.
- Features: `features/` owns screens, hooks, types, and feature-specific components.
- Services: `services/` owns fetch-based API clients.
- Navigation: `navigation/` owns root, tab, and feed navigation.
- Theme: `theme/` owns branch-aware colors and provider state.

Path aliases are configured in `frontend/tsconfig.json` and `frontend/babel.config.js`: `@features/*`, `@services/*`, `@components/*`, `@theme/*`, `@navigation/*`, `@context/*`, and related aliases.

### API Endpoints

- `GET /api/v1/health`
- `GET /api/v1/feed/`
- `GET /api/v1/summary/`
- `POST /api/v1/summary/notify`
- `POST /api/v1/ingest/updates`
- `POST /api/v1/notifications/register`

## Durable Knowledge

Use repo docs instead of hidden agent state:
- `docs/agentic/repo-map.md` for the codebase map.
- `docs/agentic/repo-map-lattice.md` for workstream, owner, and gate relationships.
- `docs/agentic/current-state-audit.md` for the latest harness migration audit.
- `docs/agentic/phase-1-codex-harness.md` for harness policy.
- `docs/agentic/codex-cloud-setup.md` for reproducible Codex cloud setup.
- `docs/agentic/templates/` for issue and implementation-plan shapes.
- `docs/architecture.md` and `docs/ingestion-sources.md` for product architecture and data-source decisions.

## Completion Rules

Before handing work back:
1. Run the smallest verification command that proves the change.
2. Run `npm run quality` when code changed, or explain any pre-existing gate blocker.
3. Run Browser or Expo web checks for browser-facing frontend changes when feasible.
4. Regenerate `docs/agentic/repo-map.md` after workflow or structure changes.
5. Report files changed, commands run, failures, and remaining risks directly.
