"""Tag tools."""

from mcp.server.fastmcp import FastMCP

from ..client import request


async def get_space_tags(space_id: str) -> list[dict]:
    """List available tags in a space.

    Args:
        space_id: The space ID.
    """
    data = await request("GET", f"/space/{space_id}/tag")
    tags = data.get("tags", [])
    return [
        {"name": t["name"], "fg_color": t.get("tag_fg"), "bg_color": t.get("tag_bg")}
        for t in tags
    ]


async def add_tag_to_task(task_id: str, tag_name: str) -> dict:
    """Add a tag to a task.

    Args:
        task_id: The task ID.
        tag_name: The tag name to add.
    """
    await request("POST", f"/task/{task_id}/tag/{tag_name}")
    return {"task_id": task_id, "tag_added": tag_name}


async def remove_tag_from_task(task_id: str, tag_name: str) -> dict:
    """Remove a tag from a task.

    Args:
        task_id: The task ID.
        tag_name: The tag name to remove.
    """
    await request("DELETE", f"/task/{task_id}/tag/{tag_name}")
    return {"task_id": task_id, "tag_removed": tag_name}


def register(mcp: FastMCP) -> None:
    for fn in (get_space_tags, add_tag_to_task, remove_tag_from_task):
        mcp.tool()(fn)
