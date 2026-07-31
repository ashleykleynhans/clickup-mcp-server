import json

import httpx
import pytest

from clickup_mcp.tools import attachments, checklists, comments, custom_fields
from clickup_mcp.tools import hierarchy, search, tags, tasks, time_tracking
from tests.conftest import mock_task


# ── Hierarchy ─────────────────────────────────────────────────────────


async def test_get_workspaces(mock_api):
    mock_api.get("/team").mock(
        return_value=httpx.Response(200, json={"teams": [{"id": "1", "name": "WS"}]})
    )
    from clickup_mcp.tools.hierarchy import get_workspaces

    assert await get_workspaces() == [{"id": "1", "name": "WS"}]


def _members_team():
    return {
        "teams": [
            {
                "id": "99",
                "members": [
                    {"user": {"id": 1, "username": "Other", "email": "other@example.com"}}
                ],
            },
            {
                "id": "9",
                "members": [
                    {"user": {"id": 10, "username": "Alice Example", "email": "alice@example.com"}},
                    {"user": {"id": 20, "username": "Bob Example", "email": "bob@example.com"}},
                ],
            },
        ]
    }


async def test_get_members_all(mock_api):
    mock_api.get("/team").mock(return_value=httpx.Response(200, json=_members_team()))
    from clickup_mcp.tools.hierarchy import get_members

    assert await get_members("9") == [
        {"id": 10, "username": "Alice Example", "email": "alice@example.com"},
        {"id": 20, "username": "Bob Example", "email": "bob@example.com"},
    ]


async def test_get_members_query_match_email(mock_api):
    mock_api.get("/team").mock(return_value=httpx.Response(200, json=_members_team()))
    from clickup_mcp.tools.hierarchy import get_members

    assert await get_members("9", "alice") == [
        {"id": 10, "username": "Alice Example", "email": "alice@example.com"},
    ]


async def test_get_members_query_no_match(mock_api):
    mock_api.get("/team").mock(return_value=httpx.Response(200, json=_members_team()))
    from clickup_mcp.tools.hierarchy import get_members

    assert await get_members("9", "zzz") == []


async def test_get_spaces(mock_api):
    mock_api.get("/team/1/space").mock(
        return_value=httpx.Response(200, json={"spaces": [{"id": "s1", "name": "Space"}]})
    )
    from clickup_mcp.tools.hierarchy import get_spaces

    assert await get_spaces("1") == [{"id": "s1", "name": "Space"}]


async def test_get_folders(mock_api):
    mock_api.get("/space/s1/folder").mock(
        return_value=httpx.Response(200, json={"folders": [{"id": "f1", "name": "Folder"}]})
    )
    from clickup_mcp.tools.hierarchy import get_folders

    assert await get_folders("s1") == [{"id": "f1", "name": "Folder"}]


async def test_get_lists(mock_api):
    mock_api.get("/folder/f1/list").mock(
        return_value=httpx.Response(200, json={"lists": [{"id": "l1", "name": "List"}]})
    )
    from clickup_mcp.tools.hierarchy import get_lists

    assert await get_lists("f1") == [{"id": "l1", "name": "List"}]


async def test_get_folderless_lists(mock_api):
    mock_api.get("/space/s1/list").mock(
        return_value=httpx.Response(200, json={"lists": [{"id": "l1", "name": "List"}]})
    )
    from clickup_mcp.tools.hierarchy import get_folderless_lists

    assert await get_folderless_lists("s1") == [{"id": "l1", "name": "List"}]


async def test_create_space(mock_api):
    mock_api.post("/team/1/space").mock(
        return_value=httpx.Response(200, json={"id": "s2", "name": "New Space"})
    )
    from clickup_mcp.tools.hierarchy import create_space

    assert await create_space("1", "New Space") == {"id": "s2", "name": "New Space"}


async def test_create_folder(mock_api):
    mock_api.post("/space/s1/folder").mock(
        return_value=httpx.Response(200, json={"id": "f2", "name": "New Folder"})
    )
    from clickup_mcp.tools.hierarchy import create_folder

    assert await create_folder("s1", "New Folder") == {"id": "f2", "name": "New Folder"}


async def test_create_list_with_content(mock_api):
    route = mock_api.post("/folder/f1/list").mock(
        return_value=httpx.Response(200, json={"id": "l2", "name": "New List"})
    )
    from clickup_mcp.tools.hierarchy import create_list

    assert await create_list("f1", "New List", content="desc") == {
        "id": "l2",
        "name": "New List",
    }
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "desc"


async def test_create_list_without_content(mock_api):
    route = mock_api.post("/folder/f1/list").mock(
        return_value=httpx.Response(200, json={"id": "l2", "name": "New List"})
    )
    from clickup_mcp.tools.hierarchy import create_list

    await create_list("f1", "New List")
    body = json.loads(route.calls[0].request.content)
    assert "content" not in body


async def test_create_folderless_list_with_content(mock_api):
    route = mock_api.post("/space/s1/list").mock(
        return_value=httpx.Response(200, json={"id": "l2", "name": "New List"})
    )
    from clickup_mcp.tools.hierarchy import create_folderless_list

    await create_folderless_list("s1", "New List", content="d")
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "d"


async def test_create_folderless_list_without_content(mock_api):
    route = mock_api.post("/space/s1/list").mock(
        return_value=httpx.Response(200, json={"id": "l2", "name": "New List"})
    )
    from clickup_mcp.tools.hierarchy import create_folderless_list

    await create_folderless_list("s1", "New List")
    body = json.loads(route.calls[0].request.content)
    assert "content" not in body
