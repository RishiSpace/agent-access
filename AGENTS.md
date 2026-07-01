# AGENTS.md

**Instructions for AI Agents** on how to use the `agent-access` tool.

This file tells you (the AI agent) exactly how to interact with the machine through this HTTP command execution server.

## Purpose

`agent-access` lets you run shell commands on the host machine and receive structured output.  
It is designed specifically so that AI agents / LLMs can perform real actions (file operations, package management, debugging, etc.) via simple HTTP calls.

## Prerequisites

Before using the tool, the following must be true:

- The `agent-access` server is running on the target machine.
- You have been given:
  - The base URL (e.g. `http://127.0.0.1:8765` or a remote address)
  - A valid auth token
- For full admin/root access, the server should have been started with `sudo`.

### Checking if the server is alive

```bash
curl "http://127.0.0.1:8765/health"
```

Expected response:

```json
{ "status": "ok", "version": "0.1.0" }
```

## Authentication

Every request to `/execute` **must** include the token using one of these methods (in order of preference):

1. Header: `X-Agent-Token: <token>`
2. Header: `Authorization: Bearer <token>`
3. Query parameter: `?token=<token>`

Example header usage:

```bash
curl -H "X-Agent-Token: abc123xyz" ...
```

## Main Endpoint

**POST** `{BASE_URL}/execute`

This is the only endpoint you need for running commands.

### Supported ways to send commands (choose the simplest that works)

#### 1. Simplest & Recommended (raw body)

```bash
curl -X POST \
  -d 'ls -la /home && whoami' \
  -H "X-Agent-Token: YOUR_TOKEN" \
  http://127.0.0.1:8765/execute
```

The entire body is treated as the shell command.

#### 2. JSON (best control)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: YOUR_TOKEN" \
  -d '{
    "command": "apt-get update && apt-get install -y htop",
    "timeout": 120,
    "cwd": "/tmp"
  }' \
  http://127.0.0.1:8765/execute
```

Supported JSON fields:
- `command` (required): The shell command to run
- `timeout` (optional): Seconds before killing the command (default 60, max 300)
- `cwd` (optional): Working directory for the command

#### 3. Query parameter (quick & dirty)

```bash
curl "http://127.0.0.1:8765/execute?token=YOUR_TOKEN&cmd=uptime"
```

> **Note**: Query parameters are logged. Prefer headers or body for sensitive commands.

## Response Format

You will always receive a JSON object:

```json
{
  "command": "the command that was executed",
  "success": true,
  "returncode": 0,
  "stdout": "standard output here\n",
  "stderr": "",
  "duration": 0.034
}
```

### Important fields

| Field        | Meaning                                      | How to use it                              |
|--------------|----------------------------------------------|--------------------------------------------|
| `success`    | `true` only if `returncode == 0`             | Primary check for "did it work?"           |
| `returncode` | Standard Unix exit code                      | `0` = success. Non-zero = failure          |
| `stdout`     | Standard output                              | Your main source of information            |
| `stderr`     | Standard error                               | Look here for error messages               |
| `duration`   | How long the command took (seconds)          | Useful for performance / timeout tuning    |

**Always** check `returncode` or `success` before trusting `stdout`.

## Recommended Patterns for Agents

### 1. Start with exploration

```bash
whoami
id
pwd
ls -la
uname -a
```

### 2. Use explicit timeouts for long operations

```json
{ "command": "apt update && apt upgrade -y", "timeout": 180 }
```

### 3. Chain commands safely

Use `&&`, `||`, `;`, and grouping:

```bash
mkdir -p /tmp/agent-work && cd /tmp/agent-work && git clone ...
```

### 4. Capture output for later reasoning

Prefer commands that produce parseable output:

- `ls -1` instead of just `ls`
- `find . -type f -name "*.py" | head -20`
- `cat file.json | jq .`
- `systemctl status my-service --no-pager`

### 5. Change directory per command

Use the `cwd` field instead of `cd` when you want to stay in one place temporarily:

```json
{ "command": "ls -la", "cwd": "/etc" }
```

### 6. Handle errors gracefully

If `returncode != 0`:

- Read `stderr` first
- Then read `stdout` (many tools print errors to stdout)
- Decide whether to retry with corrected command

## Safety Guidelines

- **Destructive commands** (rm -rf, format, drop database, etc.) should be used with extreme caution.
- Prefer `rm -i` style thinking or ask for explicit confirmation when possible.
- Use `timeout` on any command that could hang.
- Never run the server on a machine you do not control without strong network restrictions.
- Prefer `localhost` binding unless remote access is explicitly required.

## Full Example Agent Interaction

```bash
# 1. Health check
curl http://127.0.0.1:8765/health

# 2. Run a command
curl -X POST -d 'df -h' \
  -H "X-Agent-Token: $TOKEN" \
  http://127.0.0.1:8765/execute

# 3. Do something with output (in your reasoning)
# Then run follow-up commands based on results
```

## Environment Variables (when starting the server)

If you need to tell a human operator how to start the server for you:

```bash
sudo AGENT_ACCESS_TOKEN="super-secret-token-123" \
     AGENT_ACCESS_PORT=8765 \
     agent-access
```

## Troubleshooting

- 401 Unauthorized → wrong or missing token
- Connection refused → server is not running
- Timeout in response → increase the `timeout` value in the request
- Very large output is truncated at ~4MB

## Summary for Agents

1. Use `POST /execute`
2. Send the token via `X-Agent-Token` header
3. Send the command as raw body (simplest) or JSON
4. Always check `returncode` and `success`
5. Read `stdout` + `stderr`
6. Use `timeout` and `cwd` when needed
7. Be careful with destructive operations

You now have full shell access on the machine through this interface. Use it responsibly.