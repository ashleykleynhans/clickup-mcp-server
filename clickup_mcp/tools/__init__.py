"""Tool registration.

Each submodule exposes plain async functions (directly awaitable and unit
testable) plus a ``register(mcp)`` that wires them onto a ``FastMCP`` instance.
"""

from mcp.server.fastmcp import FastMCP

from . import (
    attachments,
    checklists,
    comments,
    custom_fields,
    hierarchy,
    search,
    tags,
    tasks,
    time_tracking,
)

__all__ = ["register_all"]


def register_all(mcp: FastMCP) -> None:
    """Register every tool submodule's functions onto ``mcp``."""
    for module in (
        hierarchy,
        tasks,
        tags,
        checklists,
        comments,
        search,
        time_tracking,
        custom_fields,
        attachments,
    ):
        module.register(mcp)
