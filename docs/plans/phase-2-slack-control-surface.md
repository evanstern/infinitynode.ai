# Phase 2 — Slack control surface (read → write)

## Goal
Use Slack as a safe control plane: ask questions first, then trigger actions with guardrails.

## Success criteria
- [ ] Slack DM supports read-only commands (status/space/failures)
- [ ] Write actions require confirmation (policy TBD) and are audited
- [ ] Clear help/command reference

## Scope

### In-scope
- Slack app/bot integration
- intent routing (command parsing → internal commands)
- guardrails: confirmations, allowlist, audit log

### Out-of-scope (for Phase 2)
- deep media request logic beyond a minimal “request” call

## Proposed work items (draft)
- Wire Slack messaging
- Implement read-only commands
- Implement write-action confirmation flow
- Audit log + rate limiting
- Document: `docs/runbooks/slack.md`

## Issue links
(TODO: link once Forgejo issues exist.)
