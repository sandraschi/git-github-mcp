"""Entry point for git-github-mcp."""

import asyncio

from .transport import run_server, run_server_async
from .server import mcp


def main() -> None:
    """Run the MCP server."""
    asyncio.run(run_server(mcp, server_name="git-github-mcp"))


if __name__ == "__main__":
    main()
