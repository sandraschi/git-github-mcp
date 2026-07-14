"""PyInstaller entry point — dual transport (HTTP / stdio).

When MCP_PORT is set (Tauri spawn), starts an HTTP server on that port.
Otherwise, runs stdio transport (Claude Desktop).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
host = os.environ.get("MCP_HOST", "127.0.0.1")

if port:
    sys.argv = ["run_server.py", "--mode", "http", "--host", host, "--port", str(port)]

from git_github_mcp.server import main

main()
