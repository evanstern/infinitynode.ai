# Workflow: Milestones → Issues → Execution

## Overview

Every feature, idea, or project becomes a **Forgejo milestone** on the `infinitynode` repo. The milestone gets broken into **issues** — each one a self-contained, LLM-executable work unit. A brief in `docs/briefs/` captures the high-level design; the issues capture the step-by-step.

## The Flow

```
Idea / Feature
    │
    ▼
docs/briefs/<feature>.md     ← high-level design, architecture, open questions
    │
    ▼
Forgejo Milestone             ← tracks overall progress, groups all issues
    │
    ▼
Forgejo Issues (1–20+)       ← each one is a concrete, executable task
    │
    ▼
Sub-agent picks up issue      ← lower-reasoning LLM executes it
    │
    ▼
PR → Review → Merge           ← Evan approves before merge
```

## Milestones

- **One milestone per feature/idea.** Name it clearly: `process-downloads-agent`, `sops-secret-management`, etc.
- Add a description summarizing the goal and linking to the brief: `See docs/briefs/<name>.md`
- Close the milestone when all issues are done and the feature ships.

## Issues — Writing for LLM Execution

Each issue should be **self-contained enough that a lower-reasoning model can execute it** without needing broader context. That means:

### Required in every issue body

1. **Goal** — one sentence: what does "done" look like?
2. **Context** — what files/systems are involved, any relevant background (link to brief if needed)
3. **Steps** — numbered, concrete actions:
   - Specific files to create/edit (with paths)
   - Expected inputs and outputs
   - Commands to run for validation
   - Edge cases to handle
4. **Acceptance criteria** — checkboxes the agent (or reviewer) can verify:
   - [ ] File X exists with Y content
   - [ ] `command Z` passes
   - [ ] No secrets committed
5. **Dependencies** — which issues must be done first (use `Depends on #N`)

### Sizing guidance

| Project size | Issues | Examples |
|-------------|--------|----------|
| Tiny | 1–2 | Config tweak, doc update |
| Small | 3–5 | Add a flag to a script, new cron job |
| Medium | 5–12 | New agent feature, integration |
| Large | 12–20+ | Full system (like process-downloads-agent) |

### Issue title convention

```
<type>: <clear action>
```

Examples:
- `feat: add --json output mode to process_downloads.py`
- `feat: create rules file loader for tv_name_map`
- `chore: set up cron job for post-processing agent`
- `docs: write runbook for process-downloads error handling`
- `test: validate dry-run against existing folder structure`

### Labels (suggested)

- **Priority:** `p0-critical`, `p1-high`, `p2-normal`, `p3-low`
- **Type:** `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
- **Status:** `blocked`, `needs-design`, `ready`
- **Domain:** `cron`, `backups`, `observability`, `slack`, `media`, `infra`

## Briefs (`docs/briefs/`)

- One markdown file per feature: `docs/briefs/<feature-slug>.md`
- Contains: summary, architecture, open questions, non-goals
- Links to the milestone
- **Not** step-by-step execution instructions (that's what issues are for)

Think of briefs as "the why and the shape" — issues are "the what and the how."

## Review / Push Policy

- I can edit freely and commit locally.
- **Before any `git push`:** I show what changed (diffstat + key diffs) and wait for 👍.
- For anything beyond a trivial change: push to a branch + open a PR.
- Sub-agents working issues should always use branches + PRs.

## Execution Model

When it's time to work:

1. **Coda (me)** reads the brief, creates the milestone, and writes all the issues with full detail.
2. **Sub-agents** (lower-reasoning models) pick up individual issues and execute them.
3. Each issue → branch → PR → review.
4. Evan reviews PRs (or I flag anything that needs attention).

The goal: **Evan describes what he wants. I plan it. Sub-agents build it. Evan approves.**
