# AGENTS.md - infinitynode.ai

This repository is managed by the `infinitynode-ai` orchestrator.

The orchestrator's persistent identity and operating context live at:

```text
/home/coda/agents/infinitynode-ai
```

Before doing project work here, read that agent config first, especially:

- `/home/coda/agents/infinitynode-ai/SOUL.md`
- `/home/coda/agents/infinitynode-ai/PROJECT.md`
- `/home/coda/agents/infinitynode-ai/wiki/index.md`

## Operating Model

- Project work happens from this bare-layout repo using branch worktrees.
- Use OpenCode subagents for delegated work inside OpenCode sessions.
- Subagents should ask `infinitynode-ai` for clarification when requirements are ambiguous or blocked.
- Subagents should put implementation work on branches and issue pull requests for review.
- Larger todos, feature ideas, and long-running work should be tracked on the Focus board rooted at `/home/coda/projects/infinitynode.ai`.

## Hosting Worktrees

When a branch worktree needs to be hosted for review:

1. Start the service from that worktree on a new available port.
2. Record the worktree name, branch, port, and purpose in the orchestrator config.
3. Evan will map that port through Visual Studio Code to `localhost` on his Mac.

Do not assume a port is free just because it worked in another worktree.
