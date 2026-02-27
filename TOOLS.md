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

## Local Git Notes

- Repo default branch: `main`
- Origin: `git@github.com:evanstern/infinitynode.ai.git`
- `openclaw` GitHub SSH key: `~/.ssh/id_ed25519_github_openclaw`

## NAS (Synology)

- NAS host: `jace` / `192.168.1.80`
- Mounts:
  - `/mnt/jace_coda` (coda home)
  - `/mnt/jace_complete`
  - `/mnt/jace_media`
  - `/mnt/jace_backups`
- Recycle area used by processor:
  - `/mnt/jace_complete/#recycle/process-downloads/`

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
