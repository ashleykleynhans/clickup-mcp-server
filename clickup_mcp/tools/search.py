"""Search tools."""

from mcp.server.fastmcp import FastMCP

from ..client import request


async def search_tasks(team_id: str, query: str) -> list[dict]:
    """Search for tasks across a workspace by name.

    Args:
        team_id: The workspace/team ID.
        query: Search query string.
    """
    data = await request(
        "GET",
        f"/team/{team_id}/task",
        params={"name": query, "include_closed": "true"},
    )
    tasks = data.get("tasks", [])
    return [
        {
            "id": t["id"],
            "custom_id": t.get("custom_id"),
            "name": t["name"],
            "status": t.get("status", {}).get("status"),
            "list": t.get("list", {}).get("name"),
            "url": t.get("url"),
        }
        for t in tasks
    ]


def register(mcp: FastMCP) -> None:
    mcp.tool()(search_tasks)
