"""Attachment tools (multipart uploads handled by httpx)."""

import os

from mcp.server.fastmcp import FastMCP

from ..client import request


async def get_attachments(task_id: str) -> list[dict]:
    """List attachments on a task.

    Args:
        task_id: The task ID.
    """
    data = await request("GET", f"/task/{task_id}/attachment")
    attachments = data.get("attachments", [])
    return [
        {
            "id": a.get("id"),
            "title": a.get("title"),
            "url": a.get("url"),
            "date": a.get("date"),
        }
        for a in attachments
    ]


async def add_attachment(task_id: str, file_path: str, filename: str | None = None) -> dict:
    """Upload a file attachment to a task.

    Args:
        task_id: The task ID.
        file_path: Absolute path to the file to upload.
        filename: Optional override for the uploaded filename.
    """
    name = filename or os.path.basename(file_path)
    with open(file_path, "rb") as fh:
        files = {"attachment": (name, fh.read())}
    data = await request("POST", f"/task/{task_id}/attachment", files=files)
    return {
        "id": data.get("id"),
        "url": data.get("url"),
        "task_id": data.get("task_id"),
        "title": data.get("title"),
    }


def register(mcp: FastMCP) -> None:
    for fn in (get_attachments, add_attachment):
        mcp.tool()(fn)
