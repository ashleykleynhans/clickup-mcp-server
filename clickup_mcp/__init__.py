"""ClickUp MCP server package.

Exposes :func:`create_mcp` (build a configured ``FastMCP`` with all tools) and
:func:`main` (validate config + run the server). Tool functions live in
:mod:`clickup_mcp.tools` and are plain async functions that can be called
directly (e.g. in tests) - :func:`tools.register_all` wires them onto a
``FastMCP`` instance.
"""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from . import tools
from .client import API_TOKEN
from .errors import ClickUpError

__all__ = ["create_mcp", "main", "ClickUpError"]

_ALLOWED_TRANSPORTS = {"stdio", "sse", "streamable-http"}


def create_mcp() -> FastMCP:
    """Build a FastMCP server with all ClickUp tools registered."""
    mcp = FastMCP("clickup")
    tools.register_all(mcp)
    return mcp


def _configure_logging() -> None:
    """Configure stderr logging for the package from CLICKUP_MCP_LOG_LEVEL."""
    level_name = os.getenv("CLICKUP_MCP_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    logger = logging.getLogger("clickup_mcp")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)


def main() -> None:
    """Entry point: validate config and run the MCP server."""
    _configure_logging()
    if not API_TOKEN:
        raise ClickUpError(
            "CLICKUP_API_TOKEN is not set. Copy .env.example to .env and add your token."
        )
    transport = os.getenv("CLICKUP_MCP_TRANSPORT", "stdio")
    if transport not in _ALLOWED_TRANSPORTS:
        raise ClickUpError(
            f"Unsupported CLICKUP_MCP_TRANSPORT={transport!r}. "
            f"Choose one of: {', '.join(sorted(_ALLOWED_TRANSPORTS))}."
        )
    mcp = create_mcp()
    mcp.run(transport=transport)
