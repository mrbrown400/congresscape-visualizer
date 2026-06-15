# Implementation Plan Template

Use this static plan format for Congresscape tasks that need more structure than a short issue comment. Keep durable decisions in `docs/architecture.md`, `docs/ingestion-sources.md`, or `docs/agentic/`.

## Outcome

What should be true when this work is complete?

## Context

- Task ID:
- Relevant docs:
- Relevant code:
- Constraints:

## Requirements

- Requirement 1:
- Requirement 2:
- Requirement 3:

## Files Likely To Change

- `path/to/file.py`
- `path/to/file.tsx`
- `path/to/test_file.py`

## Steps

1. Inspect current behavior and owners.
2. Make the smallest scoped change that satisfies the requirements.
3. Update docs, skills, or architecture notes only when the task changes durable behavior.
4. Run the verification commands below.

## Acceptance Criteria

- Criteria 1:
- Criteria 2:
- Criteria 3:

## Verification

- Backend: `cd backend && poetry run pytest`
- Backend lint: `cd backend && poetry run ruff check .`
- Frontend typecheck: `cd frontend && npx tsc --noEmit`
- Frontend lint: `cd frontend && npm run lint`
- Browser-facing work: Expo web or Browser smoke check

## Risks And Non-Goals

- Risk:
- Non-goal:
