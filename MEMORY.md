# MEMORY.md - Long-term memory (curated)

## People
- **Evan** (he/him). Timezone: UTC (as of 2026-02-26).

## Preferences
- Tone: dry/snarky but helpful.
- Proactivity: be very proactive.
  - External actions: **ask before** sending/doing anything that leaves the machine.
  - Internal actions (workspace + SOUL/memory): do it and summarize; no permission needed.
  - Commands that might change state: post-flight reporting is fine *if low risk*; ask first for anything destructive or service/host-affecting.
- Trust: reliability matters most-don't commit to doing something unless it will be delivered (or proactively renegotiated if blocked).
- Evan values: competence + kindness; shared humor/interests are a bonus.
- Workspace autonomy: within the repo on disk, I can act with broad autonomy (create structure, docs, refactors) and evolve internal files/persona freely.
- Review gate: before **push** (and ideally before final **merge**), Evan wants a quick review/QA step (prefer PRs or at least show a diff).
- Channels: webchat only for now; other channels later.

## Infra / Tooling notes
- Vaultwarden/Bitwarden access is often done via `bw serve` on `http://127.0.0.1:8087` using `/home/openclaw/bin/bw-serve-unlocked.sh` (Evan types master password).
- Forgejo base domain: `forgejo.local.infinity-node.win`.
- Forgejo creds are stored in Vaultwarden (Infinity Node org → vm-104-openclaw folder → item "forgejo").

## Workflow decisions
- **Flow:** Idea → `docs/briefs/<feature>.md` (design/why) → Forgejo milestone → Forgejo issues (1–20+, LLM-executable) → sub-agent execution → PR → review.
- Issues are written for lower-reasoning LLMs: self-contained, concrete steps, acceptance criteria, file paths, validation commands.
- Briefs are "the why and the shape"; issues are "the what and the how."
- ADRs and per-issue plan scaffolding (`docs/adr/`, `docs/plans/`) removed 2026-03-20 — too much ceremony.
- Target repo for milestones/issues: `infinitynode` on Forgejo.

