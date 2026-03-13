#!/usr/bin/env python3
"""ClickUp MCP Server - Manage ClickUp tasks from Claude Code."""

import os
import json
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

CLICKUP_API = "https://api.clickup.com/api/v2"
API_TOKEN = os.getenv("CLICKUP_API_TOKEN", "")

mcp = FastMCP("clickup")


def _headers() -> dict[str, str]:
    return {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json",
    }


async def _request(method: str, path: str, **kwargs: Any) -> dict | list:
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method,
            f"{CLICKUP_API}{path}",
            headers=_headers(),
            timeout=30,
            **kwargs,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()


# ── Workspace / hierarchy ────────────────────────────────────────────


@mcp.tool()
async def get_workspaces() -> str:
    """List all workspaces (teams) the authenticated user belongs to."""
    data = await _request("GET", "/team")
    teams = data.get("teams", [])
    return json.dumps(
        [{"id": t["id"], "name": t["name"]} for t in teams], indent=2
    )


@mcp.tool()
async def get_spaces(team_id: str) -> str:
    """List all spaces in a workspace.

    Args:
        team_id: The workspace/team ID.
    """
    data = await _request("GET", f"/team/{team_id}/space")
    spaces = data.get("spaces", [])
    return json.dumps(
        [{"id": s["id"], "name": s["name"]} for s in spaces], indent=2
    )


@mcp.tool()
async def get_folders(space_id: str) -> str:
    """List all folders in a space.

    Args:
        space_id: The space ID.
    """
    data = await _request("GET", f"/space/{space_id}/folder")
    folders = data.get("folders", [])
    return json.dumps(
        [{"id": f["id"], "name": f["name"]} for f in folders], indent=2
    )


@mcp.tool()
async def get_lists(folder_id: str) -> str:
    """List all lists in a folder.

    Args:
        folder_id: The folder ID.
    """
    data = await _request("GET", f"/folder/{folder_id}/list")
    lists = data.get("lists", [])
    return json.dumps(
        [{"id": l["id"], "name": l["name"]} for l in lists], indent=2
    )


@mcp.tool()
async def get_folderless_lists(space_id: str) -> str:
    """List all lists in a space that are not inside a folder.

    Args:
        space_id: The space ID.
    """
    data = await _request("GET", f"/space/{space_id}/list")
    lists = data.get("lists", [])
    return json.dumps(
        [{"id": l["id"], "name": l["name"]} for l in lists], indent=2
    )


# ── Tasks ─────────────────────────────────────────────────────────────


@mcp.tool()
async def get_tasks(
    list_id: str,
    statuses: list[str] | None = None,
    include_closed: bool = False,
    page: int = 0,
) -> str:
    """Get tasks from a list (100 per page).

    Args:
        list_id: The list ID to get tasks from.
        statuses: Optional list of statuses to filter by.
        include_closed: Whether to include closed tasks.
        page: Page number (0-indexed) for pagination.
    """
    params: dict[str, Any] = {
        "page": page,
        "include_closed": str(include_closed).lower(),
    }
    if statuses:
        for s in statuses:
            params.setdefault("statuses[]", [])
            if isinstance(params["statuses[]"], list):
                params["statuses[]"].append(s)
    data = await _request("GET", f"/list/{list_id}/task", params=params)
    tasks = data.get("tasks", [])
    return json.dumps(
        [
            {
                "id": t["id"],
                "custom_id": t.get("custom_id"),
                "name": t["name"],
                "status": t.get("status", {}).get("status"),
                "priority": t.get("priority"),
                "tags": [tag["name"] for tag in t.get("tags", [])],
                "due_date": t.get("due_date"),
                "assignees": [a.get("username") for a in t.get("assignees", [])],
                "parent": t.get("parent"),
            }
            for t in tasks
        ],
        indent=2,
    )


@mcp.tool()
async def get_task(task_id: str, include_subtasks: bool = True) -> str:
    """Get a single task by ID, optionally with subtasks.

    Args:
        task_id: The task ID.
        include_subtasks: Whether to include subtasks.
    """
    params = {"include_subtasks": str(include_subtasks).lower()}
    data = await _request("GET", f"/task/{task_id}", params=params)
    return json.dumps(
        {
            "id": data["id"],
            "custom_id": data.get("custom_id"),
            "name": data["name"],
            "description": data.get("text_content"),
            "status": data.get("status", {}).get("status"),
            "priority": data.get("priority"),
            "tags": [tag["name"] for tag in data.get("tags", [])],
            "due_date": data.get("due_date"),
            "start_date": data.get("start_date"),
            "time_estimate": data.get("time_estimate"),
            "assignees": [a.get("username") for a in data.get("assignees", [])],
            "parent": data.get("parent"),
            "subtasks": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "status": s.get("status", {}).get("status"),
                }
                for s in data.get("subtasks", [])
            ],
            "url": data.get("url"),
        },
        indent=2,
    )


@mcp.tool()
async def create_task(
    list_id: str,
    name: str,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    assignees: list[int] | None = None,
    due_date: int | None = None,
    start_date: int | None = None,
    time_estimate: int | None = None,
    parent: str | None = None,
) -> str:
    """Create a new task in a list. Set parent to create a subtask.

    Args:
        list_id: The list ID to create the task in.
        name: Task name/title.
        description: Task description (markdown supported).
        status: Task status string (must match a status in the list).
        priority: Priority: 1=urgent, 2=high, 3=normal, 4=low.
        tags: List of tag names to apply.
        assignees: List of user IDs to assign.
        due_date: Due date as unix timestamp in milliseconds.
        start_date: Start date as unix timestamp in milliseconds.
        time_estimate: Time estimate in milliseconds.
        parent: Parent task ID (makes this a subtask).
    """
    body: dict[str, Any] = {"name": name}
    if description is not None:
        body["description"] = description
    if status is not None:
        body["status"] = status
    if priority is not None:
        body["priority"] = priority
    if tags is not None:
        body["tags"] = tags
    if assignees is not None:
        body["assignees"] = assignees
    if due_date is not None:
        body["due_date"] = due_date
    if start_date is not None:
        body["start_date"] = start_date
    if time_estimate is not None:
        body["time_estimate"] = time_estimate
    if parent is not None:
        body["parent"] = parent

    data = await _request("POST", f"/list/{list_id}/task", json=body)
    return json.dumps(
        {"id": data["id"], "custom_id": data.get("custom_id"), "name": data["name"], "url": data.get("url")},
        indent=2,
    )


@mcp.tool()
async def create_task_with_subtasks(
    list_id: str,
    name: str,
    subtasks: list[str],
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
) -> str:
    """Create a task with multiple subtasks in one operation.

    Args:
        list_id: The list ID to create the task in.
        name: Parent task name.
        subtasks: List of subtask names to create.
        description: Parent task description.
        status: Status for the parent task.
        priority: Priority for the parent task (1=urgent, 2=high, 3=normal, 4=low).
        tags: Tags for the parent task.
    """
    body: dict[str, Any] = {"name": name}
    if description is not None:
        body["description"] = description
    if status is not None:
        body["status"] = status
    if priority is not None:
        body["priority"] = priority
    if tags is not None:
        body["tags"] = tags

    parent = await _request("POST", f"/list/{list_id}/task", json=body)
    parent_id = parent["id"]

    created_subtasks = []
    for st_name in subtasks:
        st = await _request(
            "POST",
            f"/list/{list_id}/task",
            json={"name": st_name, "parent": parent_id},
        )
        created_subtasks.append({"id": st["id"], "custom_id": st.get("custom_id"), "name": st["name"]})

    return json.dumps(
        {
            "id": parent_id,
            "custom_id": parent.get("custom_id"),
            "name": parent["name"],
            "url": parent.get("url"),
            "subtasks": created_subtasks,
        },
        indent=2,
    )


@mcp.tool()
async def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
    start_date: int | None = None,
    time_estimate: int | None = None,
    parent: str | None = None,
) -> str:
    """Update an existing task's fields. Only provided fields are changed.

    Args:
        task_id: The task ID to update.
        name: New task name.
        description: New description.
        status: New status string.
        priority: New priority (1=urgent, 2=high, 3=normal, 4=low).
        due_date: New due date as unix timestamp in milliseconds.
        start_date: New start date as unix timestamp in milliseconds.
        time_estimate: New time estimate in milliseconds.
        parent: New parent task ID (move to subtask).
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if status is not None:
        body["status"] = status
    if priority is not None:
        body["priority"] = priority
    if due_date is not None:
        body["due_date"] = due_date
    if start_date is not None:
        body["start_date"] = start_date
    if time_estimate is not None:
        body["time_estimate"] = time_estimate
    if parent is not None:
        body["parent"] = parent

    data = await _request("PUT", f"/task/{task_id}", json=body)
    return json.dumps(
        {
            "id": data["id"],
            "custom_id": data.get("custom_id"),
            "name": data["name"],
            "status": data.get("status", {}).get("status"),
            "url": data.get("url"),
        },
        indent=2,
    )


@mcp.tool()
async def update_task_status(task_id: str, status: str) -> str:
    """Quick helper to update just the status of a task or subtask.

    Args:
        task_id: The task ID to update.
        status: The new status string (must match a valid status in the list).
    """
    data = await _request("PUT", f"/task/{task_id}", json={"status": status})
    return json.dumps(
        {
            "id": data["id"],
            "custom_id": data.get("custom_id"),
            "name": data["name"],
            "status": data.get("status", {}).get("status"),
        },
        indent=2,
    )


@mcp.tool()
async def delete_task(task_id: str) -> str:
    """Delete a task by ID.

    Args:
        task_id: The task ID to delete.
    """
    await _request("DELETE", f"/task/{task_id}")
    return json.dumps({"deleted": True, "task_id": task_id})


# ── Tags ──────────────────────────────────────────────────────────────


@mcp.tool()
async def add_tag_to_task(task_id: str, tag_name: str) -> str:
    """Add a tag to a task.

    Args:
        task_id: The task ID.
        tag_name: The tag name to add.
    """
    await _request("POST", f"/task/{task_id}/tag/{tag_name}")
    return json.dumps({"task_id": task_id, "tag_added": tag_name})


@mcp.tool()
async def remove_tag_from_task(task_id: str, tag_name: str) -> str:
    """Remove a tag from a task.

    Args:
        task_id: The task ID.
        tag_name: The tag name to remove.
    """
    await _request("DELETE", f"/task/{task_id}/tag/{tag_name}")
    return json.dumps({"task_id": task_id, "tag_removed": tag_name})


@mcp.tool()
async def get_space_tags(space_id: str) -> str:
    """List all tags available in a space.

    Args:
        space_id: The space ID.
    """
    data = await _request("GET", f"/space/{space_id}/tag")
    tags = data.get("tags", [])
    return json.dumps(
        [{"name": t["name"], "fg_color": t.get("tag_fg"), "bg_color": t.get("tag_bg")} for t in tags],
        indent=2,
    )


# ── Checklists ────────────────────────────────────────────────────────


@mcp.tool()
async def create_checklist(task_id: str, name: str) -> str:
    """Create a checklist on a task.

    Args:
        task_id: The task ID.
        name: Checklist name.
    """
    data = await _request(
        "POST", f"/task/{task_id}/checklist", json={"name": name}
    )
    checklist = data.get("checklist", {})
    return json.dumps(
        {"id": checklist.get("id"), "name": checklist.get("name")}, indent=2
    )


@mcp.tool()
async def create_checklist_item(
    checklist_id: str, name: str, assignee: int | None = None
) -> str:
    """Add an item to a checklist.

    Args:
        checklist_id: The checklist ID.
        name: Checklist item name.
        assignee: Optional user ID to assign.
    """
    body: dict[str, Any] = {"name": name}
    if assignee is not None:
        body["assignee"] = assignee
    data = await _request(
        "POST", f"/checklist/{checklist_id}/checklist_item", json=body
    )
    return json.dumps(data.get("checklist", {}), indent=2)


# ── Comments ──────────────────────────────────────────────────────────


@mcp.tool()
async def get_task_comments(task_id: str) -> str:
    """Get all comments on a task.

    Args:
        task_id: The task ID.
    """
    data = await _request("GET", f"/task/{task_id}/comment")
    comments = data.get("comments", [])
    return json.dumps(
        [
            {
                "id": c["id"],
                "text": c.get("comment_text"),
                "user": c.get("user", {}).get("username"),
                "date": c.get("date"),
            }
            for c in comments
        ],
        indent=2,
    )


@mcp.tool()
async def add_comment(task_id: str, comment_text: str) -> str:
    """Add a comment to a task.

    Args:
        task_id: The task ID.
        comment_text: The comment text.
    """
    data = await _request(
        "POST",
        f"/task/{task_id}/comment",
        json={"comment_text": comment_text},
    )
    return json.dumps({"id": data.get("id"), "hist_id": data.get("hist_id")}, indent=2)


# ── Search ────────────────────────────────────────────────────────────


@mcp.tool()
async def search_tasks(team_id: str, query: str) -> str:
    """Search for tasks across a workspace by name.

    Args:
        team_id: The workspace/team ID.
        query: Search query string.
    """
    data = await _request(
        "GET", f"/team/{team_id}/task", params={"name": query, "include_closed": "true"}
    )
    tasks = data.get("tasks", [])
    return json.dumps(
        [
            {
                "id": t["id"],
                "custom_id": t.get("custom_id"),
                "name": t["name"],
                "status": t.get("status", {}).get("status"),
                "list": t.get("list", {}).get("name"),
                "url": t.get("url"),
            }
            for t in tasks
        ],
        indent=2,
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
