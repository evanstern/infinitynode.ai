---
name: git-workdir
description: Run git commands via OpenClaw exec without triggering exec approvals caused by shell builtins (e.g., `cd ... && git ...`). Use when executing git status/add/commit/push from the agent and you want to avoid approvals by ensuring the command starts with the git binary and setting exec workdir instead of using `cd`.
---

# Run git without exec-approval friction

## Rule

Prefer:

- `exec(command="git …", workdir="/path/to/repo")`

Avoid:

- `exec(command="cd /path/to/repo && git …")` (shell builtin → resolves to bash → may require approval)

## Patterns

### Status

- `git status -sb`

### Commit

- `git add -A`
- `git commit -m "<type>(<scope>): <subject>"`

Use Conventional Commits as defined in `AGENTS.md`.

### Push

- `git push <remote> <branch>`

If a push requires SSH identity selection, prefer an SSH host alias in `~/.ssh/config` (e.g., `forgejo-local`) and set the remote URL to `ssh://forgejo-local/<owner>/<repo>.git`.
