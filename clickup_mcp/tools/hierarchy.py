"""Workspace hierarchy tools: workspaces, members, spaces, folders, lists,
and creation of spaces / folders / lists."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import request


async def get_workspaces() -> list[dict]:
    """List all workspaces (teams) the authenticated user belongs to."""
    data = await request("GET", "/team")
    teams = data.get("teams", [])
    return [{"id": t["id"], "name": t["name"]} for t in teams]


async def get_members(team_id: str, query: str | None = None) -> list[dict]:
    """List workspace members with numeric user IDs, usernames and emails.

    Use this to resolve a person's name to the numeric ``assignees`` IDs
    required by create_task / update_task.

    Args:
        team_id: The workspace/team ID.
        query: Optional case-insensitive substring to filter members by
            username or email (e.g. "marco").
    """
    data = await request("GET", "/team")
    needle = (query or "").lower()
    members: list[dict] = []
    for team in data.get("teams", []):
        if str(team.get("id")) != str(team_id):
            continue
        for member in team.get("members", []):
            user = member.get("user", {})
            username = user.get("username") or ""
            email = user.get("email") or ""
            if needle and needle not in username.lower() and needle not in email.lower():
                continue
            members.append({"id": user.get("id"), "username": username, "email": email})
    return members


async def get_spaces(team_id: str) -> list[dict]:
    """List all spaces in a workspace.

    Args:
        team_id: The workspace/team ID.
    """
    data = await request("GET", f"/team/{team_id}/space")
    spaces = data.get("spaces", [])
    return [{"id": s["id"], "name": s["name"]} for s in spaces]


async def get_folders(space_id: str) -> list[dict]:
    """List all folders in a space.

    Args:
        space_id: The space ID.
    """
    data = await request("GET", f"/space/{space_id}/folder")
    folders = data.get("folders", [])
    return [{"id": f["id"], "name": f["name"]} for f in folders]


async def get_lists(folder_id: str) -> list[dict]:
    """List all lists in a folder.

    Args:
        folder_id: The folder ID.
    """
    data = await request("GET", f"/folder/{folder_id}/list")
    lists = data.get("lists", [])
    return [{"id": lst["id"], "name": lst["name"]} for lst in lists]


async def get_folderless_lists(space_id: str) -> list[dict]:
    """List all lists in a space that are not inside a folder.

    Args:
        space_id: The space ID.
    """
    data = await request("GET", f"/space/{space_id}/list")
    lists = data.get("lists", [])
    return [{"id": lst["id"], "name": lst["name"]} for lst in lists]


async def create_space(team_id: str, name: str) -> dict:
    """Create a space in a workspace.

    Args:
        team_id: The workspace/team ID.
        name: The new space name.
    """
    data = await request("POST", f"/team/{team_id}/space", json={"name": name})
    return {"id": data.get("id"), "name": data.get("name")}


async def create_folder(space_id: str, name: str) -> dict:
    """Create a folder in a space.

    Args:
        space_id: The space ID.
        name: The new folder name.
    """
    data = await request("POST", f"/space/{space_id}/folder", json={"name": name})
    return {"id": data.get("id"), "name": data.get("name")}


async def create_list(folder_id: str, name: str, content: str | None = None) -> dict:
    """Create a list inside a folder.

    Args:
        folder_id: The folder ID to create the list in.
        name: The new list name.
        content: Optional list description.
    """
    body: dict[str, Any] = {"name": name}
    if content is not None:
        body["content"] = content
    data = await request("POST", f"/folder/{folder_id}/list", json=body)
    return {"id": data.get("id"), "name": data.get("name")}


async def create_folderless_list(space_id: str, name: str, content: str | None = None) -> dict:
    """Create a list directly in a space (not inside any folder).

    Args:
        space_id: The space ID.
        name: The new list name.
        content: Optional list description.
    """
    body: dict[str, Any] = {"name": name}
    if content is not None:
        body["content"] = content
    data = await request("POST", f"/space/{space_id}/list", json=body)
    return {"id": data.get("id"), "name": data.get("name")}


def register(mcp: FastMCP) -> None:
    for fn in (
        get_workspaces,
        get_members,
        get_spaces,
        get_folders,
        get_lists,
        get_folderless_lists,
        create_space,
        create_folder,
        create_list,
        create_folderless_list,
    ):
        mcp.tool()(fn)
