"""Task tools: list (with pagination), get, create, create-with-subtasks,
update, update status, delete."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import request
from ..errors import ClickUpError
from ..models import TaskCreate, TaskUpdate

_PAGE_SIZE = 100  # ClickUp returns at most 100 tasks per page.
_MAX_PAGES = 200  # Safety cap so a misbehaving API can't loop forever.


def _curate(t: dict) -> dict:
    return {
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


def _tasks_params(statuses, include_closed, page) -> list[tuple[str, Any]]:
    """Build repeated query params (explicit tuples avoid fragile nested lists)."""
    params: list[tuple[str, Any]] = [
        ("page", page),
        ("include_closed", str(include_closed).lower()),
    ]
    for s in statuses or []:
        params.append(("statuses[]", s))
    return params


async def get_tasks(
    list_id: str,
    statuses: list[str] | None = None,
    include_closed: bool = False,
    page: int = 0,
    auto_paginate: bool = False,
) -> list[dict]:
    """Get tasks from a list (100 per page).

    Args:
        list_id: The list ID to get tasks from.
        statuses: Optional list of statuses to filter by.
        include_closed: Whether to include closed tasks.
        page: Page number (0-indexed) for pagination.
        auto_paginate: If True, fetch every page and return all tasks.
    """
    if auto_paginate:
        return await _get_all_tasks(list_id, statuses, include_closed)
    params = _tasks_params(statuses, include_closed, page)
    data = await request("GET", f"/list/{list_id}/task", params=params)
    return [_curate(t) for t in data.get("tasks", [])]


async def _get_all_tasks(list_id, statuses, include_closed) -> list[dict]:
    collected: list[dict] = []
    for page in range(_MAX_PAGES):
        data = await request(
            "GET", f"/list/{list_id}/task", params=_tasks_params(statuses, include_closed, page)
        )
        tasks = data.get("tasks", [])
        collected.extend(_curate(t) for t in tasks)
        has_more = data.get("has_more")
        if has_more is True:
            continue
        if has_more is False:
            break
        # No explicit signal: stop when a short page is returned.
        if len(tasks) < _PAGE_SIZE:
            break
    return collected


async def get_task(task_id: str, include_subtasks: bool = True) -> dict:
    """Get a single task by ID, optionally with subtasks.

    Args:
        task_id: The task ID.
        include_subtasks: Whether to include subtasks.
    """
    params = {"include_subtasks": str(include_subtasks).lower()}
    data = await request("GET", f"/task/{task_id}", params=params)
    return {
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
    }


async def create_task(
    list_id: str,
    name: str,
    description: str | None = None,
    markdown_content: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    assignees: list[int] | None = None,
    due_date: int | str | None = None,
    start_date: int | str | None = None,
    time_estimate: int | None = None,
    parent: str | None = None,
) -> dict:
    """Create a new task in a list. Set parent to create a subtask.

    Args:
        list_id: The list ID to create the task in.
        name: Task name/title.
        description: Plain-text task description. Markdown syntax is shown
            literally; use markdown_content for rich formatting instead.
        markdown_content: Markdown-formatted description rendered as ClickUp
            rich text. Takes precedence over description when both are given.
        status: Task status string (must match a status in the list).
        priority: Priority: 1=urgent, 2=high, 3=normal, 4=low.
        tags: List of tag names to apply.
        assignees: List of user IDs to assign.
        due_date: Due date as a unix timestamp in ms or an ISO-8601 string.
        start_date: Start date as a unix timestamp in ms or an ISO-8601 string.
        time_estimate: Time estimate in milliseconds.
        parent: Parent task ID (makes this a subtask).
    """
    body = TaskCreate(
        name=name,
        description=description,
        markdown_content=markdown_content,
        status=status,
        priority=priority,
        tags=tags,
        assignees=assignees,
        due_date=due_date,
        start_date=start_date,
        time_estimate=time_estimate,
        parent=parent,
    ).model_dump(exclude_none=True)
    data = await request("POST", f"/list/{list_id}/task", json=body)
    return {
        "id": data.get("id"),
        "custom_id": data.get("custom_id"),
        "name": data.get("name"),
        "url": data.get("url"),
    }


async def create_task_with_subtasks(
    list_id: str,
    name: str,
    subtasks: list[str],
    description: str | None = None,
    markdown_content: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Create a task with multiple subtasks in one operation.

    If a subtask fails, the parent and any already-created subtasks are
    returned with ``"partial": true`` and an ``"error"`` message so the caller
    knows the real state and can clean up if needed.

    Args:
        list_id: The list ID to create the task in.
        name: Parent task name.
        subtasks: List of subtask names to create.
        description: Plain-text parent task description. Markdown syntax is
            shown literally; use markdown_content for rich formatting instead.
        markdown_content: Markdown-formatted parent description rendered as
            ClickUp rich text. Takes precedence over description.
        status: Status for the parent task.
        priority: Priority for the parent task (1=urgent, 2=high, 3=normal, 4=low).
        tags: Tags for the parent task.
    """
    body = TaskCreate(
        name=name,
        description=description,
        markdown_content=markdown_content,
        status=status,
        priority=priority,
        tags=tags,
    ).model_dump(exclude_none=True)
    parent = await request("POST", f"/list/{list_id}/task", json=body)
    parent_id = parent.get("id")
    created: list[dict] = []
    partial = False
    error: str | None = None
    try:
        for st_name in subtasks:
            st = await request(
                "POST",
                f"/list/{list_id}/task",
                json={"name": st_name, "parent": parent_id},
            )
            created.append(
                {
                    "id": st.get("id"),
                    "custom_id": st.get("custom_id"),
                    "name": st.get("name"),
                }
            )
    except ClickUpError as exc:
        partial = True
        error = str(exc)
    result = {
        "id": parent_id,
        "custom_id": parent.get("custom_id"),
        "name": parent.get("name"),
        "url": parent.get("url"),
        "subtasks": created,
    }
    if partial:
        result["partial"] = True
        result["error"] = error
    return result



async def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    markdown_content: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | str | None = None,
    start_date: int | str | None = None,
    time_estimate: int | None = None,
    parent: str | None = None,
) -> dict:
    """Update an existing task's fields. Only provided fields are changed.

    Args:
        task_id: The task ID to update.
        name: New task name.
        description: New plain-text description. Markdown syntax is shown
            literally; use markdown_content for rich formatting instead.
        markdown_content: New markdown-formatted description rendered as
            ClickUp rich text. Takes precedence over description.
        status: New status string.
        priority: New priority (1=urgent, 2=high, 3=normal, 4=low).
        due_date: New due date as a unix timestamp in ms or ISO-8601 string.
        start_date: New start date as a unix timestamp in ms or ISO-8601 string.
        time_estimate: New time estimate in milliseconds.
        parent: New parent task ID (move to subtask).
    """
    body = TaskUpdate(
        name=name,
        description=description,
        markdown_content=markdown_content,
        status=status,
        priority=priority,
        due_date=due_date,
        start_date=start_date,
        time_estimate=time_estimate,
        parent=parent,
    ).model_dump(exclude_none=True)
    data = await request("PUT", f"/task/{task_id}", json=body)
    return {
        "id": data.get("id"),
        "custom_id": data.get("custom_id"),
        "name": data.get("name"),
        "status": data.get("status", {}).get("status"),
        "url": data.get("url"),
    }


async def update_task_status(task_id: str, status: str) -> dict:
    """Quick helper to update just the status of a task or subtask.

    Args:
        task_id: The task ID to update.
        status: The new status string (must match a valid status in the list).
    """
    data = await request("PUT", f"/task/{task_id}", json={"status": status})
    return {
        "id": data.get("id"),
        "custom_id": data.get("custom_id"),
        "name": data.get("name"),
        "status": data.get("status", {}).get("status"),
    }


async def delete_task(task_id: str) -> dict:
    """Delete a task by ID.

    If the task does not exist, a ClickUpError (404) is raised rather than
    pretending the deletion succeeded.

    Args:
        task_id: The task ID to delete.
    """
    await request("DELETE", f"/task/{task_id}")
    return {"deleted": True, "task_id": task_id}


def register(mcp: FastMCP) -> None:
    for fn in (
        get_tasks,
        get_task,
        create_task,
        create_task_with_subtasks,
        update_task,
        update_task_status,
        delete_task,
    ):
        mcp.tool()(fn)

