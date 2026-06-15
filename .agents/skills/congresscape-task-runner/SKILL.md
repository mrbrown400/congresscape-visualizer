---
name: congresscape-task-runner
description: Use for normal Congresscape implementation tasks driven by an issue, branch, or user request.
---

# Congresscape Task Runner

Use this skill for day-to-day implementation.

## Workflow

1. Read `AGENTS.md`.
2. Identify the issue-shaped frame: goal, context, constraints, and done-when.
3. Inspect existing backend/frontend owners before editing.
4. Keep changes scoped to the request and current branch.
5. Update durable docs only when behavior, architecture, or workflow changes.
6. Run the smallest verification command that proves the change.

## Commands

```bash
npm run agent:repo-map
npm run quality
cd backend && poetry run pytest
cd frontend && npx tsc --noEmit
```

## Closeout

Report files changed, commands run, remaining blockers, and any branch or issue context used. Do not claim a gate passes unless the fresh command output confirms it.
