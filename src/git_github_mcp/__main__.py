"""Entry point for git-github-mcp."""

import asyncio

from .server import mcp
from .transport import run_server


def main() -> None:
    """Run the MCP server."""
    asyncio.run(run_server(mcp, server_name="git-github-mcp"))


if __name__ == "__main__":
    main()
