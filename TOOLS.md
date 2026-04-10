# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Model Tiering (as of 2026-03-20)

Budget: ~$200/mo target

| Role | Model | Alias | Rationale |
|------|-------|-------|-----------|
| Main session (me) | Claude Sonnet 4 | `sonnet` | Good balance of cost + capability for daily work |
| High-reasoning (planning, architecture) | Claude Opus 4.6 | `opus` | Use `/model opus` when deep reasoning needed |
| Sub-agent execution (issues) | Claude Sonnet 4 | `sonnet` | Default for sub-agents |
| Simple/bulk tasks | Haiku 4.5 (`claude-haiku-4-5`) or GPT-5.4 mini | `haiku` / `GPT` | Cheap for mechanical work |

**How to escalate:** Evan or I can switch to Opus mid-session with `/model opus` when a task needs stronger reasoning, then back to Sonnet with `/model sonnet`.

**Cost estimates (per 1M tokens):**
- Opus 4.6: $5 in / $25 out
- Sonnet 4: $3 in / $15 out
- Haiku 4.5: $1 in / $5 out
- GPT-5.4 mini: $0.75 in / $4.50 out

## Local Git Notes

- Repo default branch: `main`
- Origin: `git@github.com:evanstern/infinitynode.ai.git`
- `openclaw` GitHub SSH key: `~/.ssh/id_ed25519_github_openclaw`

## Vaultwarden / Bitwarden (bw CLI)

- Evan runs `bw serve` (unlocked) locally for agent access at: `http://127.0.0.1:8087`
- Helper script (prompts interactively): `/home/openclaw/bin/bw-serve-unlocked.sh`
- Forgejo creds live in Vaultwarden:
  - org: **Infinity Node**
  - folder: **vm-104-openclaw**
  - item name: **forgejo**
- Forgejo base domain: `forgejo.local.infinity-node.win` (use http if needed; SSH for git when available)
- Forgejo API docs reference: https://forgejo.org/docs/latest/user/api-usage/
  - Swagger UI (if enabled): `http(s)://<host>/api/swagger`
  - OpenAPI JSON: `http(s)://<host>/swagger.v1.json`
  - API settings (paging limits, etc.): `GET /api/v1/settings/api`
- Note: outbound network calls from this agent may be gated by approvals; local `127.0.0.1` calls work.

## NAS (Synology)

- NAS host: `jace` / `192.168.1.80`
- Mounts:
  - `/mnt/jace_coda` (coda home)
  - `/mnt/jace_complete`
  - `/mnt/jace_media`
  - `/mnt/jace_backups`
- Recycle area used by processor:
  - `/mnt/jace_complete/#recycle/process-downloads/`

## Voice / sag (ElevenLabs TTS)

- Binary: `~/go/bin/sag`
- API key: `~/.config/sag/api-key` — must pass `--api-key-file ~/.config/sag/api-key` explicitly (env var only works when `.bashrc` is sourced)
- Default voice: Roger (laid-back, casual, resonant)
- **Upload flow** (Slack): generate to workspace, then use `message` tool with `filePath`
  ```bash
  ~/go/bin/sag speak --api-key-file ~/.config/sag/api-key -o ~/.openclaw/workspace/voice-reply.mp3 "text"
  ```
  Then: `message(action=send, filePath=~/.openclaw/workspace/voice-reply.mp3)`
- `/tmp` paths are blocked by the message tool — always write to workspace
- Slack scope required: `files:write` (added 2026-03-22)
- Use sparingly — best for storytime, humor, or when voice adds real value

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
