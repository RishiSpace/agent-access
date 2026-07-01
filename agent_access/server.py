"""
agent-access server.

Runs an HTTP server that accepts commands via simple HTTP requests (JSON or plain text),
executes them (intended to be run as root/admin), and returns stdout/stderr + return code.

SECURITY WARNING:
  - This executes arbitrary shell commands. Only expose on trusted networks / localhost.
  - Always use a strong auth token.
  - By default binds to 127.0.0.1.
  - Start the process with elevated privileges (sudo) if you need commands to run as root.
"""

import os
import subprocess
import time
from typing import Optional

from flask import Flask, request, jsonify, abort

DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"
DEFAULT_TIMEOUT = 60
MAX_OUTPUT_SIZE = 1024 * 1024 * 4  # 4 MiB cap on combined output


def create_app(auth_token: str, allow_cors: bool = False) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["AUTH_TOKEN"] = auth_token

    if allow_cors:
        # Very permissive CORS - only use for local dev / trusted environments
        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Agent-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            return response

    def _check_auth() -> bool:
        """Check auth token from multiple convenient locations."""
        token = app.config["AUTH_TOKEN"]
        if not token:
            return False

        # Header options (preferred)
        for header in ("X-Agent-Token", "Authorization", "X-Auth-Token"):
            val = request.headers.get(header, "")
            if header == "Authorization":
                # Accept "Bearer xxx" or just "xxx"
                if val.lower().startswith("bearer "):
                    val = val[7:]
            if val and val == token:
                return True

        # Query param (convenient for curl one-liners, but appears in logs)
        qtoken = request.args.get("token") or request.args.get("auth")
        if qtoken and qtoken == token:
            return True

        return False

    def _require_auth():
        if not _check_auth():
            abort(401, description="Unauthorized: invalid or missing token")

    def _truncate(text: str, max_bytes: int = MAX_OUTPUT_SIZE) -> str:
        data = text.encode("utf-8", errors="replace")
        if len(data) <= max_bytes:
            return text
        return data[:max_bytes].decode("utf-8", errors="replace") + "\n... [output truncated]"

    def _run_command(command: str, timeout: int, cwd: Optional[str] = None) -> dict:
        """Execute the command and return structured result."""
        started = time.time()
        result = {
            "command": command,
            "success": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "duration": None,
        }

        if not command or not command.strip():
            result["stderr"] = "Empty command"
            result["returncode"] = 1
            result["duration"] = time.time() - started
            return result

        try:
            # Use shell=True so that complex one-liners, pipes, etc. work naturally.
            # This is intentional for an agent command server.
            proc = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                executable="/bin/bash" if os.name != "nt" else None,
            )
            result["returncode"] = proc.returncode
            result["stdout"] = _truncate(proc.stdout or "")
            result["stderr"] = _truncate(proc.stderr or "")
            result["success"] = proc.returncode == 0
        except subprocess.TimeoutExpired as e:
            result["stderr"] = _truncate((e.stderr or "").decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
            result["stdout"] = _truncate((e.stdout or "").decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""))
            result["returncode"] = 124  # conventional timeout code
            result["stderr"] += f"\n[ERROR] Command timed out after {timeout}s"
            result["success"] = False
        except Exception as e:
            result["stderr"] = f"[ERROR] Failed to execute command: {e}"
            result["returncode"] = 1
            result["success"] = False

        result["duration"] = round(time.time() - started, 3)
        return result

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "version": "0.1.0",
        })

    @app.route("/execute", methods=["GET", "POST", "OPTIONS"])
    def execute():
        _require_auth()

        if request.method == "OPTIONS":
            return "", 204

        # Determine the command
        command = None
        timeout = DEFAULT_TIMEOUT
        cwd = None

        # Get raw body early (important for supporting plain -d 'command' in curl)
        raw_body = (request.get_data(as_text=True) or "").strip()

        if request.is_json:
            data = request.get_json(silent=True) or {}
            command = data.get("command") or data.get("cmd")
            timeout = int(data.get("timeout", DEFAULT_TIMEOUT))
            cwd = data.get("cwd")
        else:
            # Form data (explicit fields)
            if request.form:
                command = request.form.get("command") or request.form.get("cmd")
                if request.form.get("timeout"):
                    try:
                        timeout = int(request.form.get("timeout"))
                    except ValueError:
                        pass
                cwd = request.form.get("cwd")

            # Raw body: treat entire body as command if no explicit form field matched.
            # This makes `curl -X POST -d 'ls -la'` work nicely.
            if not command and raw_body:
                command = raw_body

        # Also support ?cmd=... or ?command=... query params as fallback
        if not command:
            command = (
                request.args.get("command")
                or request.args.get("cmd")
            )
            if request.args.get("timeout"):
                try:
                    timeout = int(request.args.get("timeout"))
                except ValueError:
                    pass
            cwd = cwd or request.args.get("cwd")

        if timeout < 1:
            timeout = DEFAULT_TIMEOUT
        if timeout > 300:
            timeout = 300  # hard cap for safety

        if not command:
            return jsonify({
                "success": False,
                "error": "No command provided. Send JSON {command: '...'} or use form/raw body or ?cmd=...",
                "returncode": 1,
            }), 400

        result = _run_command(command, timeout=timeout, cwd=cwd)
        return jsonify(result), 200

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "agent-access",
            "endpoints": {
                "POST /execute": "Run a command. Auth required.",
                "GET /health": "Health check",
            },
            "auth": "Send token via X-Agent-Token header, Authorization: Bearer <token>, or ?token= query param",
            "examples": {
                "curl_json": 'curl -X POST http://127.0.0.1:8765/execute -H "X-Agent-Token: YOUR_TOKEN" -H "Content-Type: application/json" -d \'{"command": "whoami"}\'',
                "curl_simple": 'curl -X POST -d "ls -la" -H "X-Agent-Token: YOUR_TOKEN" http://127.0.0.1:8765/execute',
                "curl_query": 'curl "http://127.0.0.1:8765/execute?token=YOUR_TOKEN&cmd=uptime"',
            }
        })

    return app


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    auth_token: Optional[str] = None,
    allow_cors: bool = False,
):
    """Run the development server (Flask built-in)."""
    if not auth_token:
        # Generate a session token if none provided
        import secrets
        auth_token = secrets.token_urlsafe(24)
        print(f"[agent-access] No token provided. Generated one for this session:")
        print(f"  AGENT_ACCESS_TOKEN={auth_token}")
        print("  Use it in requests or set the env var next time.")

    app = create_app(auth_token=auth_token, allow_cors=allow_cors)

    print(f"[agent-access] Starting server on http://{host}:{port}")
    print(f"[agent-access] Auth token required. Send via X-Agent-Token header or ?token= param")
    print(f"[agent-access] Example: curl -X POST -d 'whoami' -H 'X-Agent-Token: {auth_token}' http://{host}:{port}/execute")
    print(f"[agent-access] WARNING: Commands run with the privileges of the server process (run with sudo for root).")

    # Use Flask development server (fine for this use case)
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
