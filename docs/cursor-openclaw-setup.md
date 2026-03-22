# Cursor ↔ OpenClaw ACP Setup

_Last updated: 2026-03-20 UTC_

## How it works

Cursor (a VS Code fork) doesn't speak ACP natively, but there's a VS Code
extension called **ACP Client** that does. It already ships with OpenClaw as a
pre-configured agent. The extension spawns `openclaw acp` as a stdio subprocess,
which bridges to the remote OpenClaw Gateway over WebSocket.

```
Cursor → ACP Client extension → openclaw acp (stdio) → SSH tunnel → Gateway (ws://127.0.0.1:18789)
```

## Server-side status (verified)

- Gateway: running, loopback-only, port 18789
- `openclaw acp` bridge: tested and working
- Gateway token file: `~/.openclaw/gateway.token` (created)
- ACP init handshake: confirmed (protocolVersion 1, agent: openclaw-acp)

## What Evan needs to do

### Step 1: Install OpenClaw CLI on your dev machine

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

Requires Node 22.16+ (Node 24 preferred). Verify with `openclaw --version`.

### Step 2: Open an SSH tunnel

```bash
ssh -N -L 18789:127.0.0.1:18789 <your-ssh-user>@192.168.1.104
```

This makes the remote Gateway appear at `ws://127.0.0.1:18789` locally.

Leave this running in a terminal tab (or use `-f` to background it, or add it
to your SSH config as a persistent tunnel).

### Step 3: Save the Gateway token locally

```bash
mkdir -p ~/.openclaw && chmod 700 ~/.openclaw
printf '%s' '6e450547136fe6f9bc1f7a4b08246eab54d0e6655e8502dd' > ~/.openclaw/gateway.token
chmod 600 ~/.openclaw/gateway.token
```

### Step 4: Sanity-check the ACP bridge

```bash
openclaw acp client --server-args --url ws://127.0.0.1:18789 --token-file ~/.openclaw/gateway.token
```

This is an interactive debug client. Type a message and you should get a
response from Coda. `Ctrl+C` to exit.

### Step 5: Install the ACP Client extension in Cursor

1. Open Cursor
2. Go to Extensions (`Cmd+Shift+X` / `Ctrl+Shift+X`)
3. Search for **"ACP Client"** by formulahendry
4. Install it

### Step 6: Configure the OpenClaw agent

Open Cursor Settings JSON (`Cmd+Shift+P` → "Preferences: Open User Settings (JSON)") and add:

```json
{
  "acp.agents": {
    "OpenClaw (Coda)": {
      "command": "openclaw",
      "args": [
        "acp",
        "--url", "ws://127.0.0.1:18789",
        "--token-file", "${userHome}/.openclaw/gateway.token"
      ],
      "env": {
        "OPENCLAW_HIDE_BANNER": "1",
        "OPENCLAW_SUPPRESS_NOTES": "1"
      }
    }
  }
}
```

**Note:** If `${userHome}` doesn't resolve in Cursor's extension context, use
the absolute path instead (e.g. `/Users/evan/.openclaw/gateway.token` on macOS
or `/home/evan/.openclaw/gateway.token` on Linux).

### Step 7: Connect

1. Click the ACP icon in the Cursor Activity Bar (left sidebar)
2. Select **"OpenClaw (Coda)"**
3. Start chatting

## Optional: target a specific session

By default, each ACP connection gets an isolated session (`acp:<uuid>`).

To reuse the main agent session (shared with Slack):

```json
"args": [
  "acp",
  "--url", "ws://127.0.0.1:18789",
  "--token-file", "${userHome}/.openclaw/gateway.token",
  "--session", "agent:main:main"
]
```

To get a dedicated but persistent session for Cursor work:

```json
"args": [
  "acp",
  "--url", "ws://127.0.0.1:18789",
  "--token-file", "${userHome}/.openclaw/gateway.token",
  "--session", "agent:main:cursor"
]
```

## Troubleshooting

- **"command not found: openclaw"** → Make sure `$(npm prefix -g)/bin` is on
  your PATH. Check with `npm prefix -g` and add to `~/.zshrc` or `~/.bashrc`.
- **Connection refused on 18789** → SSH tunnel isn't running. Start it first.
- **Auth errors** → Token mismatch. Verify the token file matches the Gateway's
  `gateway.auth.token`.
- **Extension not showing ACP icon** → Reload Cursor window (`Cmd+Shift+P` →
  "Developer: Reload Window").

## Security notes

- The Gateway token is an operator-level credential. Treat it like a password.
- Keep the Gateway on loopback. SSH tunnel is the safe remote access pattern.
- Prefer `--token-file` over `--token` to keep the secret out of process listings.
