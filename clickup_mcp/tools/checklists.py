"""Checklist tools: create, list, update item, delete item, delete checklist."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import request
from ..dates import parse_datetime_to_ms


async def create_checklist(task_id: str, name: str) -> dict:
    """Create a checklist on a task.

    Args:
        task_id: The task ID.
        name: Checklist name.
    """
    data = await request("POST", f"/task/{task_id}/checklist", json={"name": name})
    checklist = data.get("checklist", {})
    return {"id": checklist.get("id"), "name": checklist.get("name")}


async def get_checklists(task_id: str) -> list[dict]:
    """List all checklists (and their items) on a task.

    Args:
        task_id: The task ID.
    """
    data = await request("GET", f"/task/{task_id}/checklist")
    checklists = data.get("checklists", [])
    return [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "resolved": c.get("resolved"),
            "items": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "resolved": item.get("resolved"),
                    "assignee": item.get("assignee"),
                }
                for item in c.get("items", [])
            ],
        }
        for c in checklists
    ]


async def create_checklist_item(
    checklist_id: str, name: str, assignee: int | None = None
) -> dict:
    """Add an item to a checklist.

    Args:
        checklist_id: The checklist ID.
        name: Checklist item name.
        assignee: Optional user ID to assign.
    """
    body: dict[str, Any] = {"name": name}
    if assignee is not None:
        body["assignee"] = assignee
    data = await request("POST", f"/checklist/{checklist_id}/checklist_item", json=body)
    return data.get("checklist", {})


async def update_checklist_item(
    checklist_id: str,
    checklist_item_id: str,
    name: str | None = None,
    resolved: bool | None = None,
    assignee: int | None = None,
    due_date: int | str | None = None,
) -> dict:
    """Update a checklist item (rename, mark complete/incomplete, assign, set due date).

    Args:
        checklist_id: The checklist ID.
        checklist_item_id: The checklist item ID.
        name: New item name.
        resolved: Mark the item complete (True) or incomplete (False).
        assignee: User ID to assign.
        due_date: Due date as a unix timestamp in ms or an ISO-8601 string.
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if resolved is not None:
        body["resolved"] = resolved
    if assignee is not None:
        body["assignee"] = assignee
    if due_date is not None:
        body["due_date"] = parse_datetime_to_ms(due_date)
    data = await request(
        "PUT", f"/checklist/{checklist_id}/checklist_item/{checklist_item_id}", json=body
    )
    return data.get("checklist", {})


async def delete_checklist_item(checklist_id: str, checklist_item_id: str) -> dict:
    """Delete a checklist item.

    Args:
        checklist_id: The checklist ID.
        checklist_item_id: The checklist item ID.
    """
    await request(
        "DELETE", f"/checklist/{checklist_id}/checklist_item/{checklist_item_id}"
    )
    return {"deleted": True, "checklist_item_id": checklist_item_id}


async def delete_checklist(checklist_id: str) -> dict:
    """Delete a checklist (and all its items).

    Args:
        checklist_id: The checklist ID.
    """
    await request("DELETE", f"/checklist/{checklist_id}")
    return {"deleted": True, "checklist_id": checklist_id}


def register(mcp: FastMCP) -> None:
    for fn in (
        create_checklist,
        get_checklists,
        create_checklist_item,
        update_checklist_item,
        delete_checklist_item,
        delete_checklist,
    ):
        mcp.tool()(fn)
