# Codex Cloud Setup

Use this when configuring a Codex cloud environment for Congresscape. The goal is to reproduce the local gates without adding a second agentic harness.

## Environment

Use a Python 3.11+ runtime for the backend and Node.js 20+ for the Expo frontend.

Backend environment variables:

```text
DATABASE_URL
OPENAI_API_KEY
CONGRESS_API_KEY
BACKEND_CORS_ORIGINS
```

Frontend environment variables:

```text
EXPO_PUBLIC_API_BASE_URL
```

Do not put secret values in the repository. Use Codex environment settings.

## Setup Script

Configure the Codex cloud setup script as:

```bash
bash scripts/codex-cloud-setup.sh
```

The script checks runtime versions, runs `poetry install` in `backend/`, and runs `npm ci` in `frontend/`. It does not create `.env`, write secrets, enable MCP servers, create code-index databases, or run harness installers.

To run the local quality gate during setup cache creation, set:

```text
CONGRESSCAPE_CODEX_SETUP_VERIFY=1
```

Leave that unset for normal setup if you only want dependency installation.

## Database

For fast local smoke tests, `DATABASE_URL` may point at SQLite with `sqlite+aiosqlite:///./congresscape.db`.

For production-like checks, use PostgreSQL with pgvector:

```bash
docker compose up -d db
docker compose exec db psql -U postgres -d congresscape -c "CREATE EXTENSION IF NOT EXISTS vector"
```

The current code has SQLite-compatible model changes, so verify pgvector-specific behavior before relying on vector search or persisted embeddings.

## Verification Commands

Standard repo gate:

```bash
npm run quality
```

Backend-only gate:

```bash
cd backend && poetry run pytest && poetry run ruff check .
```

Frontend-only gate:

```bash
cd frontend && npx tsc --noEmit && npm run lint
```

Browser-facing changes should run an Expo web or Browser smoke check when the dependency set can start cleanly.

## Harness Policy

Cloud setup should stay aligned with the repo-local harness policy:

- Use `AGENTS.md`, `.agents/skills/`, GitHub, repo docs, `rg`, language references, and direct verification commands first.
- Do not enable raw MCP servers, code-index runtimes, background memory stores, or orchestration UIs in cloud setup by default.
- Evaluate global harness candidates in the user-level Codex harness before adopting anything into this repo.
