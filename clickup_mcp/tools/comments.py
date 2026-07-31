"""Comment tools."""

from mcp.server.fastmcp import FastMCP

from ..client import request


async def get_task_comments(task_id: str) -> list[dict]:
    """Get all comments on a task.

    Args:
        task_id: The task ID.
    """
    data = await request("GET", f"/task/{task_id}/comment")
    comments = data.get("comments", [])
    return [
        {
            "id": c["id"],
            "text": c.get("comment_text"),
            "user": c.get("user", {}).get("username"),
            "date": c.get("date"),
        }
        for c in comments
    ]


async def add_comment(task_id: str, comment_text: str) -> dict:
    """Add a comment to a task.

    Args:
        task_id: The task ID.
        comment_text: The comment text.
    """
    data = await request(
        "POST", f"/task/{task_id}/comment", json={"comment_text": comment_text}
    )
    return {"id": data.get("id"), "hist_id": data.get("hist_id")}


def register(mcp: FastMCP) -> None:
    for fn in (get_task_comments, add_comment):
        mcp.tool()(fn)
