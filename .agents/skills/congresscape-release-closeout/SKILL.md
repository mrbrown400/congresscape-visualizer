---
name: congresscape-release-closeout
description: Use for Congresscape final verification, branch handoff, and PR-ready summaries.
---

# Congresscape Release Closeout

Use this skill before handing Congresscape work back.

## Checklist

1. Run `npm run agent:repo-map` after workflow or structure changes.
2. Run `npm run quality` when code changed, or report the pre-existing gate blocker.
3. Run targeted backend/frontend checks for the changed surface.
4. Run Browser or Expo web checks for browser-facing tasks when feasible.
5. Mention the issue key in branch names, commit messages, or PR descriptions when one exists.

## Response Shape

Report:

- Files changed.
- Commands run and whether they passed.
- Known failures and whether they are pre-existing.
- Remaining risks or follow-up candidates.
