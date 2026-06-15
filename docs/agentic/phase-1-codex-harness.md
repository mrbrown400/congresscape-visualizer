# Phase 1 Codex Harness

Phase 1 keeps Congresscape's agentic engineering harness small, inspectable, and Codex-native. It adopts useful ideas as static repo guidance before adding any new runtime dependency.

## Baseline

Congresscape's active harness pieces are:

- `AGENTS.md` for repo entry instructions.
- `.agents/skills/` for focused Codex workflows.
- GitHub for branch, commit, pull request, and review flow.
- `docs/agentic/` for agent workflow docs.
- `docs/architecture.md` and `docs/ingestion-sources.md` for durable system knowledge.
- Backend gates through Poetry, pytest, and Ruff.
- Frontend gates through Expo, TypeScript, ESLint when installed, and Browser or Expo web smoke checks.

## Adopted References

| Source | Phase 1 Use | Boundary |
| --- | --- | --- |
| `github/spec-kit` | Reference for spec shape, acceptance criteria, and task planning. | Do not add a second task tracker or spec runtime by default. |
| Agent Skills structure | Reference for focused `SKILL.md` files and progressive disclosure. | Do not bulk import skills. |
| External skill catalogs | Discovery catalogs for possible Codex skills. | Review individual skills before adoption. |
| Superpowers | Selective workflow support for planning, debugging, review, parallel investigation, and verification. | Do not duplicate Congresscape repo-local skills. |
| Static repo maps | Checked-in Markdown maps and relationship notes. | Reject daemon, database, MCP, or hidden-memory defaults. |

## Static Implementations

- `docs/agentic/templates/linear-issue-spec.md` gives issues a spec and acceptance-criteria shape.
- `docs/agentic/templates/implementation-plan.md` gives larger tasks a repeatable plan shape.
- `docs/agentic/skills-portability.md` records the Agent Skills portability standard for `.agents/skills/*/SKILL.md`.
- `docs/agentic/codex-skill-discovery.md` records the external skill-catalog intake process.
- `docs/agentic/repo-map.md` records the generated codebase map.
- `docs/agentic/repo-map-lattice.md` records the static workstream relationship map.
- `docs/agentic/current-state-audit.md` records the current branch, app, and harness audit.

## Non-Goals

Do not add these to Congresscape by default:

- New daemon.
- New MCP server.
- New persistent harness database, vector store, or hidden memory layer.
- New orchestration UI.
- Alternate agent shell.
- Broad token optimizer that hides command output.

These belong in the user-level Codex harness first. Congresscape should only adopt a new harness runtime after a bounded benchmark proves it fills a real gap and does not hide verification evidence.

## Intake Rule

Before adding any new skill, MCP server, memory layer, code indexer, or orchestration tool, use `.agents/skills/congresscape-harness-curation/SKILL.md`.

The default answer is no unless the tool has:

1. A concrete Congresscape workflow gap.
2. Low overlap with Codex, `rg`, language references, GitHub, Browser, repo docs, and existing skills.
3. A small install and security surface.
4. A local and Codex-cloud-compatible path.
5. A benchmark proving it saves time or catches defects without hiding evidence.
