---
name: congresscape-harness-curation
description: Use before adding or evaluating agentic harness tools, Codex skills, MCP servers, memory stores, code indexers, or orchestration systems for Congresscape.
---

# Congresscape Harness Curation

Use this skill when a task proposes a new agentic-engineering tool or workflow dependency.

## Default Posture

Congresscape is Codex-native and intentionally small:

- GitHub owns branches, commits, pull requests, and review.
- `AGENTS.md` and `.agents/skills/` own repeatable agent workflow.
- `docs/agentic/`, `docs/architecture.md`, and `docs/ingestion-sources.md` own durable project knowledge.
- Backend and frontend commands own verification.

Do not add an agentic harness daemon, MCP server, database, alternate agent shell, hidden memory layer, or orchestration UI by default. This does not ban product data storage or normal app infrastructure.

## Approved Phase 1 References

- `github/spec-kit`: reference for issue/spec shape and acceptance criteria.
- Agent Skills structure: reference for `SKILL.md` shape and progressive disclosure.
- External skill catalogs: discovery only.
- Superpowers: use selectively when the installed skill directly fits the task.
- Static Markdown repo maps: preferred over runtime indexes.

## Intake Checklist

Before recommending adoption, answer:

1. What Congresscape workflow is failing today?
2. Why do Codex, `rg`, language references, GitHub, Browser, repo docs, and existing skills not already cover it?
3. What files, services, credentials, network access, hooks, or background processes would the tool add?
4. Can it run as static Markdown, an npm script, or a one-shot local command instead of a daemon, MCP server, or harness database?
5. How will the tool work in both local Codex and Codex cloud environments?
6. What benchmark proves the tool saves time or catches defects without hiding evidence?

Reject the tool for Congresscape if the answer is unclear.

## Where Outcomes Belong

- Put active plans in issue descriptions or comments.
- Put durable architecture decisions in `docs/architecture.md` or `docs/ingestion-sources.md`.
- Put agent workflow policy in `AGENTS.md`, `.agents/skills/`, or `docs/agentic/`.
- Put cross-repo personal memory outside this repo only when it is useful outside Congresscape.
