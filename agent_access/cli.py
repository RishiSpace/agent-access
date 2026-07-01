"""CLI entry point for agent-access."""

import argparse
import os
import sys

from agent_access.server import run_server, DEFAULT_HOST, DEFAULT_PORT


def main():
    parser = argparse.ArgumentParser(
        prog="agent-access",
        description="Start the agent-access command execution server. "
                    "AI agents (or curl/wget) can POST commands which will be executed "
                    "and results returned. Run the server as root (sudo) if you need admin privileges.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=["serve"],
        help="Subcommand (default: serve)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("AGENT_ACCESS_HOST", DEFAULT_HOST),
        help=f"Host interface to bind to (default: {DEFAULT_HOST}). "
             "Use 0.0.0.0 to allow remote connections (DANGEROUS).",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.environ.get("AGENT_ACCESS_PORT", DEFAULT_PORT)),
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("AGENT_ACCESS_TOKEN"),
        help="Auth token required for all requests. "
             "If omitted, a random one will be generated and printed.",
    )
    parser.add_argument(
        "--allow-cors",
        action="store_true",
        help="Add permissive CORS headers (only for trusted dev environments).",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="Show version and exit.",
    )

    args = parser.parse_args()

    if args.version:
        from agent_access import __version__
        print(f"agent-access {__version__}")
        sys.exit(0)

    if args.command == "serve":
        # Strong warning if binding publicly
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!! WARNING: Binding to a non-localhost interface        !!!")
            print("!!! This exposes a command execution endpoint to network !!!")
            print("!!! Only do this if you fully trust all clients.         !!!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        run_server(
            host=args.host,
            port=args.port,
            auth_token=args.token,
            allow_cors=args.allow_cors,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
