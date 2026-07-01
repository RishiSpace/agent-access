# AI-SystemAssist

A tiny, easy-to-use HTTP server that lets AI agents (or humans with curl/wget) send shell commands to be executed on the machine and receive the output back.

**Intended use**: Give an LLM / agent the ability to run commands on a machine over HTTP and get results.

## ⚠️ SECURITY WARNING

- This server executes **arbitrary shell commands**.
- Run it **only on machines you control**.
- Default binding is `127.0.0.1` (localhost only).
- **Always** use a strong auth token.
- To execute commands **as root/admin**, start the server with `sudo`.
- Do **not** expose this on the public internet without strong additional protections (VPN, firewall, TLS reverse proxy, etc.).

## Installation

From the source directory (development):

```bash
pip install -e .
```

Or build & install:

```bash
pip install .
```

## Quick Start

```bash
# Start the server (will generate a token if none provided)
sudo ai-systemassist

# Or with explicit token and options
AI_SYSTEMASSIST_TOKEN=my-super-secret-token ai-systemassist --host 127.0.0.1 --port 8765
```

Environment variables (also supported):
- `AI_SYSTEMASSIST_TOKEN`
- `AI_SYSTEMASSIST_HOST`
- `AI_SYSTEMASSIST_PORT`

## Usage from curl / wget (very easy)

### 1. With generated or provided token

```bash
TOKEN="your-token-here"

# Simple - raw POST body is treated as the command
curl -X POST -d 'whoami && id' \
  -H "X-Agent-Token: $TOKEN" \
  http://127.0.0.1:8765/execute

# JSON body (recommended for complex cases)
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: $TOKEN" \
  -d '{"command": "ls -la /", "timeout": 30}' \
  http://127.0.0.1:8765/execute

# Query param (quick and dirty - visible in logs)
curl "http://127.0.0.1:8765/execute?token=$TOKEN&cmd=uptime"
```

### 2. Example response

```json
{
  "command": "whoami && id",
  "success": true,
  "returncode": 0,
  "stdout": "root\nuid=0(root) gid=0(root) groups=0(root)\n",
  "stderr": "",
  "duration": 0.012
}
```

### Using wget

```bash
wget -qO- --post-data='ls -l' \
  --header="X-Agent-Token: $TOKEN" \
  http://127.0.0.1:8765/execute
```

## Endpoints

| Endpoint     | Method | Description                              |
|--------------|--------|------------------------------------------|
| `/execute`   | POST   | Run a command. Auth required.            |
| `/execute`   | GET    | Same as POST (useful for simple queries) |
| `/health`    | GET    | Basic health + version info              |
| `/`          | GET    | API information + examples               |

### Request formats supported on `/execute`

- JSON: `{ "command": "ls", "timeout": 30, "cwd": "/tmp" }`
- Form: `command=ls` or `cmd=ls`
- Raw body: `echo hello | cat`
- Query params: `?cmd=ls&token=...`

Auth can be sent as:
- Header: `X-Agent-Token: xxx`
- Header: `Authorization: Bearer xxx`
- Header: `X-Auth-Token: xxx`
- Query: `?token=xxx`

## Running as Admin / Root

```bash
sudo ai-systemassist --token "super-secret"
# or
sudo -E ai-systemassist   # preserves env vars including AI_SYSTEMASSIST_TOKEN
```

All commands will then run as root.

## Configuration / CLI

```bash
ai-systemassist --help
```

Options:
- `--host`, `--port`
- `--token`
- `--allow-cors`

## Python usage (advanced)

```python
from ai_systemassist.server import create_app, run_server

app = create_app(auth_token="mytoken")
# then run with your own WSGI server if desired (gunicorn, waitress, etc.)
```

## Development

```bash
pip install -e ".[dev]"
```

## For AI Agents

See **[AGENTS.md](AGENTS.md)** for detailed instructions written specifically for AI agents and LLMs on how to use this tool effectively (authentication, request formats, response handling, best practices, and safety guidelines).

## License

MIT
