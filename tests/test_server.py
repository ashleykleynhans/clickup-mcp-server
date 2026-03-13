import json

import httpx
import pytest
import respx

from server import (
    _headers,
    _request,
    get_workspaces,
    get_spaces,
    get_folders,
    get_lists,
    get_folderless_lists,
    get_tasks,
    get_task,
    create_task,
    create_task_with_subtasks,
    update_task,
    update_task_status,
    delete_task,
    add_tag_to_task,
    remove_tag_from_task,
    get_space_tags,
    create_checklist,
    create_checklist_item,
    get_task_comments,
    add_comment,
    search_tasks,
    main,
    CLICKUP_API,
)
from tests.conftest import mock_task


# ── _headers / _request ──────────────────────────────────────────────


def test_headers():
    h = _headers()
    assert "Authorization" in h
    assert h["Content-Type"] == "application/json"


async def test_request_json(mock_api):
    mock_api.get("/test").mock(return_value=httpx.Response(200, json={"ok": True}))
    result = await _request("GET", "/test")
    assert result == {"ok": True}


async def test_request_204(mock_api):
    mock_api.delete("/gone").mock(return_value=httpx.Response(204))
    result = await _request("DELETE", "/gone")
    assert result == {}


async def test_request_empty_body(mock_api):
    mock_api.post("/empty").mock(return_value=httpx.Response(200, content=b""))
    result = await _request("POST", "/empty")
    assert result == {}


async def test_request_http_error(mock_api):
    mock_api.get("/fail").mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await _request("GET", "/fail")


# ── Hierarchy ─────────────────────────────────────────────────────────


async def test_get_workspaces(mock_api):
    mock_api.get("/team").mock(
        return_value=httpx.Response(200, json={"teams": [{"id": "1", "name": "WS"}]})
    )
    result = json.loads(await get_workspaces())
    assert result == [{"id": "1", "name": "WS"}]


async def test_get_spaces(mock_api):
    mock_api.get("/team/1/space").mock(
        return_value=httpx.Response(200, json={"spaces": [{"id": "s1", "name": "Space"}]})
    )
    result = json.loads(await get_spaces("1"))
    assert result == [{"id": "s1", "name": "Space"}]


async def test_get_folders(mock_api):
    mock_api.get("/space/s1/folder").mock(
        return_value=httpx.Response(200, json={"folders": [{"id": "f1", "name": "Folder"}]})
    )
    result = json.loads(await get_folders("s1"))
    assert result == [{"id": "f1", "name": "Folder"}]


async def test_get_lists(mock_api):
    mock_api.get("/folder/f1/list").mock(
        return_value=httpx.Response(200, json={"lists": [{"id": "l1", "name": "List"}]})
    )
    result = json.loads(await get_lists("f1"))
    assert result == [{"id": "l1", "name": "List"}]


async def test_get_folderless_lists(mock_api):
    mock_api.get("/space/s1/list").mock(
        return_value=httpx.Response(200, json={"lists": [{"id": "l2", "name": "FList"}]})
    )
    result = json.loads(await get_folderless_lists("s1"))
    assert result == [{"id": "l2", "name": "FList"}]


# ── Tasks ─────────────────────────────────────────────────────────────


async def test_get_tasks_basic(mock_api):
    task = mock_task()
    mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"tasks": [task]})
    )
    result = json.loads(await get_tasks("l1"))
    assert len(result) == 1
    assert result[0]["id"] == "task1"
    assert result[0]["custom_id"] == "CU-1"
    assert result[0]["status"] == "open"


async def test_get_tasks_with_statuses(mock_api):
    mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    result = json.loads(await get_tasks("l1", statuses=["open", "closed"], include_closed=True, page=1))
    assert result == []


async def test_get_task_with_subtasks(mock_api):
    subtask = {"id": "sub1", "name": "Sub", "status": {"status": "todo"}}
    task = mock_task(
        text_content="desc",
        tags=["bug"],
        assignees=["alice"],
        subtasks=[subtask],
    )
    mock_api.get("/task/task1").mock(
        return_value=httpx.Response(200, json=task)
    )
    result = json.loads(await get_task("task1"))
    assert result["custom_id"] == "CU-1"
    assert result["description"] == "desc"
    assert result["tags"] == ["bug"]
    assert result["assignees"] == ["alice"]
    assert len(result["subtasks"]) == 1
    assert result["subtasks"][0]["status"] == "todo"


async def test_get_task_no_subtasks(mock_api):
    task = mock_task()
    mock_api.get("/task/task1").mock(
        return_value=httpx.Response(200, json=task)
    )
    result = json.loads(await get_task("task1", include_subtasks=False))
    assert result["subtasks"] == []


async def test_create_task_minimal(mock_api):
    resp_task = mock_task(id="new1", custom_id="CU-NEW")
    mock_api.post("/list/l1/task").mock(
        return_value=httpx.Response(200, json=resp_task)
    )
    result = json.loads(await create_task("l1", "Test Task"))
    assert result["id"] == "new1"
    assert result["custom_id"] == "CU-NEW"


async def test_create_task_all_fields(mock_api):
    resp_task = mock_task(id="new2", custom_id="CU-2")
    mock_api.post("/list/l1/task").mock(
        return_value=httpx.Response(200, json=resp_task)
    )
    result = json.loads(
        await create_task(
            list_id="l1",
            name="Full Task",
            description="desc",
            status="open",
            priority=1,
            tags=["urgent"],
            assignees=[123],
            due_date=1700000000000,
            start_date=1699000000000,
            time_estimate=3600000,
            parent="parent1",
        )
    )
    assert result["id"] == "new2"
    req = mock_api.calls[-1].request
    body = json.loads(req.content)
    assert body["name"] == "Full Task"
    assert body["description"] == "desc"
    assert body["status"] == "open"
    assert body["priority"] == 1
    assert body["tags"] == ["urgent"]
    assert body["assignees"] == [123]
    assert body["due_date"] == 1700000000000
    assert body["start_date"] == 1699000000000
    assert body["time_estimate"] == 3600000
    assert body["parent"] == "parent1"


async def test_create_task_with_subtasks(mock_api):
    parent_resp = mock_task(id="p1", custom_id="CU-P")
    sub1_resp = mock_task(id="s1", custom_id="CU-S1", name="Sub 1")
    sub2_resp = mock_task(id="s2", custom_id="CU-S2", name="Sub 2")
    mock_api.post("/list/l1/task").mock(
        side_effect=[
            httpx.Response(200, json=parent_resp),
            httpx.Response(200, json=sub1_resp),
            httpx.Response(200, json=sub2_resp),
        ]
    )
    result = json.loads(
        await create_task_with_subtasks(
            list_id="l1",
            name="Parent",
            subtasks=["Sub 1", "Sub 2"],
            description="pdesc",
            status="open",
            priority=2,
            tags=["feature"],
        )
    )
    assert result["id"] == "p1"
    assert result["custom_id"] == "CU-P"
    assert len(result["subtasks"]) == 2
    assert result["subtasks"][0]["custom_id"] == "CU-S1"
    # Verify parent body
    parent_body = json.loads(mock_api.calls[0].request.content)
    assert parent_body["description"] == "pdesc"
    assert parent_body["status"] == "open"
    assert parent_body["priority"] == 2
    assert parent_body["tags"] == ["feature"]
    # Verify subtask body has parent
    sub_body = json.loads(mock_api.calls[1].request.content)
    assert sub_body["parent"] == "p1"


async def test_create_task_with_subtasks_minimal(mock_api):
    parent_resp = mock_task(id="p2", custom_id=None)
    mock_api.post("/list/l1/task").mock(
        return_value=httpx.Response(200, json=parent_resp)
    )
    result = json.loads(
        await create_task_with_subtasks("l1", "Parent", subtasks=[])
    )
    assert result["id"] == "p2"
    assert result["subtasks"] == []


async def test_update_task_all_fields(mock_api):
    resp = mock_task(id="t1", custom_id="CU-U", name="Updated", status="done")
    mock_api.put("/task/t1").mock(
        return_value=httpx.Response(200, json=resp)
    )
    result = json.loads(
        await update_task(
            "t1",
            name="Updated",
            description="new desc",
            status="done",
            priority=3,
            due_date=1700000000000,
            start_date=1699000000000,
            time_estimate=7200000,
            parent="p1",
        )
    )
    assert result["custom_id"] == "CU-U"
    assert result["status"] == "done"
    body = json.loads(mock_api.calls[0].request.content)
    assert body["name"] == "Updated"
    assert body["description"] == "new desc"
    assert body["priority"] == 3
    assert body["due_date"] == 1700000000000
    assert body["start_date"] == 1699000000000
    assert body["time_estimate"] == 7200000
    assert body["parent"] == "p1"


async def test_update_task_partial(mock_api):
    resp = mock_task(id="t1", name="Same", status="open")
    mock_api.put("/task/t1").mock(
        return_value=httpx.Response(200, json=resp)
    )
    result = json.loads(await update_task("t1", status="open"))
    assert result["id"] == "t1"
    body = json.loads(mock_api.calls[0].request.content)
    assert body == {"status": "open"}


async def test_update_task_status(mock_api):
    resp = mock_task(id="t1", custom_id="CU-1", status="in progress")
    mock_api.put("/task/t1").mock(
        return_value=httpx.Response(200, json=resp)
    )
    result = json.loads(await update_task_status("t1", "in progress"))
    assert result["custom_id"] == "CU-1"
    assert result["status"] == "in progress"


async def test_delete_task(mock_api):
    mock_api.delete("/task/t1").mock(return_value=httpx.Response(204))
    result = json.loads(await delete_task("t1"))
    assert result == {"deleted": True, "task_id": "t1"}


# ── Tags ──────────────────────────────────────────────────────────────


async def test_add_tag_to_task(mock_api):
    mock_api.post("/task/t1/tag/bug").mock(return_value=httpx.Response(200, json={}))
    result = json.loads(await add_tag_to_task("t1", "bug"))
    assert result == {"task_id": "t1", "tag_added": "bug"}


async def test_remove_tag_from_task(mock_api):
    mock_api.delete("/task/t1/tag/bug").mock(return_value=httpx.Response(200, json={}))
    result = json.loads(await remove_tag_from_task("t1", "bug"))
    assert result == {"task_id": "t1", "tag_removed": "bug"}


async def test_get_space_tags(mock_api):
    mock_api.get("/space/s1/tag").mock(
        return_value=httpx.Response(
            200, json={"tags": [{"name": "bug", "tag_fg": "#fff", "tag_bg": "#f00"}]}
        )
    )
    result = json.loads(await get_space_tags("s1"))
    assert result == [{"name": "bug", "fg_color": "#fff", "bg_color": "#f00"}]


# ── Checklists ────────────────────────────────────────────────────────


async def test_create_checklist(mock_api):
    mock_api.post("/task/t1/checklist").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1", "name": "Todo"}})
    )
    result = json.loads(await create_checklist("t1", "Todo"))
    assert result == {"id": "cl1", "name": "Todo"}


async def test_create_checklist_item_no_assignee(mock_api):
    mock_api.post("/checklist/cl1/checklist_item").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1", "items": []}})
    )
    result = json.loads(await create_checklist_item("cl1", "Item 1"))
    assert "id" in result


async def test_create_checklist_item_with_assignee(mock_api):
    mock_api.post("/checklist/cl1/checklist_item").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1"}})
    )
    result = json.loads(await create_checklist_item("cl1", "Item 2", assignee=42))
    body = json.loads(mock_api.calls[0].request.content)
    assert body["assignee"] == 42


# ── Comments ──────────────────────────────────────────────────────────


async def test_get_task_comments(mock_api):
    mock_api.get("/task/t1/comment").mock(
        return_value=httpx.Response(
            200,
            json={
                "comments": [
                    {
                        "id": "c1",
                        "comment_text": "hello",
                        "user": {"username": "alice"},
                        "date": "1700000000000",
                    }
                ]
            },
        )
    )
    result = json.loads(await get_task_comments("t1"))
    assert len(result) == 1
    assert result[0]["text"] == "hello"
    assert result[0]["user"] == "alice"


async def test_add_comment(mock_api):
    mock_api.post("/task/t1/comment").mock(
        return_value=httpx.Response(200, json={"id": "c2", "hist_id": "h1"})
    )
    result = json.loads(await add_comment("t1", "my comment"))
    assert result == {"id": "c2", "hist_id": "h1"}


# ── Search ────────────────────────────────────────────────────────────


async def test_search_tasks(mock_api):
    task = mock_task(list_name="My List")
    mock_api.get("/team/1/task").mock(
        return_value=httpx.Response(200, json={"tasks": [task]})
    )
    result = json.loads(await search_tasks("1", "test"))
    assert len(result) == 1
    assert result[0]["custom_id"] == "CU-1"
    assert result[0]["list"] == "My List"


# ── main ──────────────────────────────────────────────────────────────


def test_main(monkeypatch):
    called = {}

    def fake_run(transport):
        called["transport"] = transport

    monkeypatch.setattr("server.mcp.run", fake_run)
    main()
    assert called["transport"] == "stdio"
