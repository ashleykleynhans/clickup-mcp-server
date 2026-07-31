"""Time tracking tools (ClickUp API v2).

Endpoints used (see https://clickup.com/api ):

* ``GET  /team/{team_id}/time_entries``           - list entries
* ``GET  /team/{team_id}/time_entries/current``    - running timer
* ``POST /team/{team_id}/time_entries``           - log a completed entry
* ``POST /team/{team_id}/time_entries/start``     - start the running timer
* ``POST /team/{team_id}/time_entries/stop``      - stop the running timer
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import request
from ..dates import parse_datetime_to_ms


def _curate_entry(e: dict) -> dict:
    user = e.get("user")
    username = user.get("username") if isinstance(user, dict) else user
    return {
        "id": e.get("id"),
        "task": e.get("tid") or e.get("task"),
        "user": username,
        "description": e.get("description"),
        "billable": e.get("billable"),
        "start": e.get("start"),
        "end": e.get("end"),
        "duration": e.get("duration"),
        "tags": [t.get("name") for t in (e.get("tags") or [])],
        "url": e.get("url"),
    }


def _first_entry(data) -> dict:
    """Extract a single time entry from various ClickUp response shapes."""
    if not isinstance(data, dict):
        return {}
    items = data.get("data")
    if isinstance(items, list):
        return items[0] if items else {}
    return data


async def get_time_entries(
    team_id: str,
    start_date: int | str | None = None,
    end_date: int | str | None = None,
    assignee: list[int] | None = None,
) -> list[dict]:
    """List time entries in a workspace, optionally filtered by date range / assignee.

    Args:
        team_id: The workspace/team ID.
        start_date: Filter start (ms or ISO-8601 string).
        end_date: Filter end (ms or ISO-8601 string).
        assignee: Optional list of user IDs to filter by.
    """
    params: list[tuple[str, Any]] = []
    if start_date is not None:
        params.append(("start_date", str(parse_datetime_to_ms(start_date))))
    if end_date is not None:
        params.append(("end_date", str(parse_datetime_to_ms(end_date))))
    for uid in assignee or []:
        params.append(("assignee[]", uid))
    data = await request("GET", f"/team/{team_id}/time_entries", params=params or None)
    if isinstance(data, list):
        entries = data
    else:
        entries = data.get("data", [])
    return [_curate_entry(e) for e in entries if isinstance(e, dict)]


async def get_current_timer(team_id: str) -> dict:
    """Get the currently running time entry for the authenticated user.

    Args:
        team_id: The workspace/team ID.
    """
    data = await request("GET", f"/team/{team_id}/time_entries/current")
    entry = _first_entry(data)
    running = bool(data.get("running")) if isinstance(data, dict) else bool(entry)
    return {"running": running, "entry": _curate_entry(entry) if entry else None}


async def create_time_entry(
    team_id: str,
    task_id: str,
    start: int | str,
    duration: int,
    description: str | None = None,
    billable: bool = False,
    assignee: int | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Log a (completed) time entry on a task. Does not start the running timer.

    Args:
        team_id: The workspace/team ID.
        task_id: The task ID to log time against.
        start: Start time (ms or ISO-8601 string).
        duration: Duration in milliseconds.
        description: Optional description.
        billable: Whether the entry is billable.
        assignee: Optional user ID.
        tags: Optional tag names.
    """
    body: dict[str, Any] = {
        "tid": task_id,
        "start": parse_datetime_to_ms(start),
        "duration": duration,
        "billable": billable,
    }
    if description is not None:
        body["description"] = description
    if assignee is not None:
        body["assignee"] = assignee
    if tags is not None:
        body["tags"] = tags
    data = await request("POST", f"/team/{team_id}/time_entries", json=body)
    return _curate_entry(_first_entry(data))


async def start_timer(
    team_id: str,
    task_id: str,
    description: str | None = None,
    billable: bool = False,
    tags: list[str] | None = None,
) -> dict:
    """Start the running timer against a task.

    Args:
        team_id: The workspace/team ID.
        task_id: The task ID to track time against.
        description: Optional description.
        billable: Whether the entry is billable.
        tags: Optional tag names.
    """
    body: dict[str, Any] = {"tid": task_id, "billable": billable}
    if description is not None:
        body["description"] = description
    if tags is not None:
        body["tags"] = tags
    data = await request("POST", f"/team/{team_id}/time_entries/start", json=body)
    return _curate_entry(_first_entry(data))


async def stop_timer(team_id: str) -> dict:
    """Stop the currently running timer.

    Args:
        team_id: The workspace/team ID.
    """
    data = await request("POST", f"/team/{team_id}/time_entries/stop")
    return _curate_entry(_first_entry(data))


def register(mcp: FastMCP) -> None:
    for fn in (get_time_entries, get_current_timer, create_time_entry, start_timer, stop_timer):
        mcp.tool()(fn)
