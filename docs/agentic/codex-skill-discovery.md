# Codex Skill Discovery

Use this process before adopting an external skill or skill-library pattern into Congresscape.

## Intake Flow

1. Define the repeated Congresscape workflow the skill would improve.
2. Compare against Codex built-ins, `rg`, language references, existing repo-local skills, and current docs.
3. Review the source skill for commands, network behavior, file writes, credentials, package installs, and hidden state.
4. Prefer adapting one small static `SKILL.md` over importing a bundle.
5. Add or update `docs/agentic/skills-portability.md` notes if the skill changes the local standard.
6. Verify the adopted skill on one real task before recommending wider use.

## Default Decision

Reject or monitor the skill unless it saves time, catches defects, or reduces repeated decision work without adding broad runtime surface.

## Where Outcomes Belong

- Repo-local workflow policy: `AGENTS.md` or `.agents/skills/`.
- Durable project decisions: `docs/architecture.md`, `docs/ingestion-sources.md`, or `docs/agentic/`.
- Cross-repo personal preference: user-level memory only when useful outside Congresscape.
