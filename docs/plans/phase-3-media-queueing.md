# Phase 3 — Media queueing (“queue The Wire”)

## Goal
Make media requests one-step from chat, routed through a stable integration layer.

## Success criteria
- [ ] Request TV/Movie by title (optionally season/quality)
- [ ] De-dupe / already-exists behavior is sane
- [ ] Clear reporting back to chat (what happened + next steps)
- [ ] Failures are actionable (missing indexers, auth, not found)

## Integration options
- Overseerr/Jellyseerr (preferred if present)
- Direct Sonarr/Radarr API calls

## Proposed work items (draft)
- Choose integration target
- Implement request flow + options
- Add dry-run mode
- Add runbook + troubleshooting

## Issue links
(TODO: link once Forgejo issues exist.)
