# Workflow: Issues (Forgejo) + Docs (Repo)

## Source of truth

- **TODOs / work queue:** Forgejo **Issues** (canonical)
- **Planning / design / runbooks:** this repo under `docs/`

Principle: chat is for discussion; issues/docs are for memory.

## When to create what

### Create/Update a Forgejo Issue when:
- there is an actionable piece of work
- work should survive chat scrollback
- we need a clear owner/state/priority

### Create/Update a Doc when:
- the work needs design decisions or sequencing
- future-you will ask “why did we do this?”
- it’s operational (backup/restore/incident)

## Linking conventions

- Each doc should link to its relevant Issues/Projects.
- Each Issue that needs design should link back to the doc section.

Suggested pattern:
- Issue body contains a **Design** section with a link to `docs/plans/...`
- Doc contains an **Issue Links** section with bullet links to Forgejo issues

## Labels (suggested)

- `phase-1`, `phase-2`, `phase-3`
- `cron`, `backups`, `observability`, `slack`, `media`
- `blocked`, `needs-design`, `good-first`

(We can adjust to match how you like to scan a board.)

## Review / push policy

Default:
- I can edit freely and commit locally.
- **Before any `git push`:** I’ll show you what changed (diffstat + key diffs) and wait for a 👍.
- When it’s more than a tiny change, I’ll prefer: push to a branch + open a PR for your review.

## Definition of Done (default)

- Clear acceptance criteria satisfied
- Logs/metrics/alerts updated if relevant
- Runbook updated if this affects operations
- No secrets committed
