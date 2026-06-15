# Issue Spec Template

Use this as a static issue-body template for Congresscape work. It borrows the useful spec shape from `github/spec-kit` without adding another task system or runtime.

## Outcome

Describe the user-facing or agent-facing result in one short paragraph.

## Context

- Current behavior:
- Relevant files:
- Related issue:
- Source/provenance constraints:

## Requirements

- Requirement 1:
- Requirement 2:
- Requirement 3:

## Acceptance Criteria

- Given..., when..., then...
- Given..., when..., then...
- Verification evidence is attached or summarized before closeout.

## Non-Goals

- Out of scope:
- Do not change:

## Verification

- `cd backend && poetry run pytest`
- `cd backend && poetry run ruff check .`
- `cd frontend && npx tsc --noEmit`
- `cd frontend && npm run lint`
- Browser-facing work: Expo web or Browser smoke check

## Notes

- Dependencies:
- Follow-up candidates:
