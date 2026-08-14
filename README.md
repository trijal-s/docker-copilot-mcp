# docker-copilot-mcp
A local MCP server that lets Claude inspect and safely manage Docker containers
on your machine — built as a hands-on project to learn the Model Context
Protocol (tools, transports, state, and safety-gated destructive actions).

## What it does

- **Read-only inspection**: list containers, get detailed status, fetch logs,
  check system health (CPU/memory/disk)
- **Safe destructive actions**: restart a container, but only after a
  two-step confirmation flow — the agent must first request a plan + token,
  then explicitly confirm before anything actually happens
- **Scoped**: only containers on an explicit whitelist can ever be restarted,
  regardless of what the agent is asked to do
- **Audited**: every tool call (especially restarts) is logged to a local
  SQLite database with timestamp, arguments, result, and success/failure

## Why this project

Most MCP tutorials stop at "here's a tool that returns data." The interesting
and hard part of building real agent tooling is deciding what an agent should
be allowed to do *without asking*, and what it must *never* do without a
human explicitly confirming. This project exists to practice that boundary,
not just the MCP plumbing.

## Architecture

Claude Desktop (MCP client) → stdio transport → FastMCP server (server.py)
→ Tools (list_containers, get_container_status, get_container_logs,
get_system_health, restart_container) → Safety Gate (scope check →
confirmation token → validate → execute) → Docker Client + Audit Log (SQLite)

## The safety model

Every destructive tool (currently just `restart_container`) goes through a
gate before touching Docker:

1. **Scope check** — is this target even allowed? The server maintains an
   explicit whitelist (`safety/scope.py`); anything outside it is refused
   immediately, no matter how the request is phrased.
2. **Dry run by default** — calling `restart_container` without a
   `confirmation_token` never restarts anything. It returns a plan
   description and a token bound to that exact action (tool + target +
   parameters).
3. **Explicit confirmation** — only a second call, with the matching token,
   actually executes. Tokens are single-use and expire after 2 minutes, so a
   stale or reused confirmation can't silently trigger an old, possibly
   outdated action.
4. **Audit trail** — both the dry-run request and the real execution are
   logged to SQLite, so there's always a record of what was proposed and
   what actually happened.

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Requires Docker Desktop running locally.

## Running

Manually (for testing):
```bash
python src/server.py
```

Via Claude Desktop: add to your config:
```json
{
  "mcpServers": {
    "homelab-ops": {
      "command": "/absolute/path/to/venv/Scripts/python.exe",
      "args": ["/absolute/path/to/src/server.py"]
    }
  }
}
```

## Tools

| Tool | Type | Description |
|---|---|---|
| `list_containers` | read-only | List all containers, running or stopped |
| `get_container_status` | read-only | Detailed status for one container |
| `get_container_logs` | read-only | Recent logs from a container |
| `get_system_health` | read-only | Host CPU / memory / disk usage |
| `restart_container` | **destructive, gated** | Restart a container (requires confirmation) |

## Tests

```bash
pytest tests/test_safety_gate.py -v
```

## What I learned building this

- The difference between MCP tools (actions) and the transport/routing layer
- Why destructive tool calls need a confirmation flow, not just try/except
- How to scope an agent's permissions explicitly, not just via prompt instructions
- Debugging a live MCP integration end-to-end, including finding that Claude
  Desktop reads config from a sandboxed AppData path, not the documented default

## Possible extensions

- HTTP transport + OAuth for remote/shared access
- systemd service management alongside Docker
- Config-driven scope whitelist instead of hardcoded list
- `/diagnose <container>` prompt template for guided investigation
