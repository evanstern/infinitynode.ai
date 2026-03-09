# Phase 1 — Cron reliability + observability

## Goal
Make scheduled jobs boring: consistent, debuggable, and loud when broken.

## Success criteria
- [ ] Each job has consistent logging, exit codes, and timeouts
- [ ] Failures notify (and do not spam)
- [ ] Daily digest summarizing what ran + what failed
- [ ] Basic host signals: disk space + stalled downloads + backup freshness

## Scope

### In-scope
- job wrapper / runner standard
- log locations + rotation policy
- notifications (channel TBD)
- digest report

### Out-of-scope (for Phase 1)
- Slack command surface
- media requesting/queueing

## Proposed work items (draft)
- Standard job runner wrapper (timeout, lock, retries, env)
- Standard logging format + location
- Failure notification + daily digest
- Health checks: disk free thresholds, large growth, stalled downloads
- Document: “How to add a new scheduled job”

## Issue links
(TODO: link once Forgejo issues exist.)
