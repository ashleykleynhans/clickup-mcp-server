"""Custom field tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import request


async def get_list_custom_fields(list_id: str) -> list[dict]:
    """List custom fields defined on a list.

    Args:
        list_id: The list ID.
    """
    data = await request("GET", f"/list/{list_id}/field")
    fields = data.get("fields", [])
    return [
        {
            "id": f.get("id"),
            "name": f.get("name"),
            "type": f.get("type"),
            "type_config": f.get("type_config"),
            "date_created": f.get("date_created"),
        }
        for f in fields
    ]


async def set_task_custom_field(task_id: str, field_id: str, value: Any) -> dict:
    """Set a custom field value on a task.

    Args:
        task_id: The task ID.
        field_id: The custom field ID.
        value: The value to set (format depends on the field type).
    """
    data = await request("POST", f"/task/{task_id}/field/{field_id}", json={"value": value})
    return data.get("field", {})


def register(mcp: FastMCP) -> None:
    for fn in (get_list_custom_fields, set_task_custom_field):
        mcp.tool()(fn)
