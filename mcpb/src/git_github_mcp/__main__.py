"""Entry point for git-github-mcp."""

import asyncio

from .server import mcp


def main() -> None:
    """Run the MCP server."""
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
