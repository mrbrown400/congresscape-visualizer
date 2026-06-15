---
name: congresscape-planning
description: Use for Congresscape task plans, migration plans, architecture decisions, and issue planning.
---

# Congresscape Planning

Use this skill before changing shared API contracts, database models, ingestion data flow, notification behavior, or frontend navigation architecture.

## Inputs

- Relevant issue or user request.
- Current files and docs that own the behavior.
- Database/runtime constraints.
- Data-source or provenance constraints for government data.

## Planning Format

1. State the user-facing or agent-facing outcome.
2. List files or modules likely to change.
3. Call out backend, frontend, database, and ingestion boundaries.
4. Define acceptance criteria before implementation.
5. Identify backend, frontend, and browser checks.
6. Put durable decisions in `docs/architecture.md`, `docs/ingestion-sources.md`, or `docs/agentic/`.

Use `docs/agentic/templates/linear-issue-spec.md` for issue bodies and `docs/agentic/templates/implementation-plan.md` for larger implementation plans.

## Harness Changes

When planning workflow or skill edits, preserve the focused Agent Skills-style `SKILL.md` shape and keep behavior repo-local. Use `.agents/skills/congresscape-harness-curation/SKILL.md` before adding runtime infrastructure.
