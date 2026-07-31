import json

import httpx
import pytest

from clickup_mcp.errors import ClickUpError
from clickup_mcp.tools import tasks as tasks_mod
from clickup_mcp.tools.tasks import (
    _tasks_params,
    create_task,
    create_task_with_subtasks,
    delete_task,
    get_task,
    get_tasks,
    update_task,
    update_task_status,
)
from tests.conftest import mock_task


# ── _tasks_params (#6 repeated params) ──────────────────────────────


def test_tasks_params_with_statuses():
    assert _tasks_params(["todo", "done"], True, 2) == [
        ("page", 2),
        ("include_closed", "true"),
        ("statuses[]", "todo"),
        ("statuses[]", "done"),
    ]


def test_tasks_params_without_statuses():
    assert _tasks_params(None, False, 0) == [
        ("page", 0),
        ("include_closed", "false"),
    ]


# ── get_tasks ─────────────────────────────────────────────────────────


async def test_get_tasks_single_page(mock_api):
    mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(
            200,
            json={"tasks": [mock_task(id="t1", name="T", tags=["bug"], assignees=["alice"])]},
        )
    )
    assert await get_tasks("l1") == [
        {
            "id": "t1",
            "custom_id": "CU-1",
            "name": "T",
            "status": "open",
            "priority": None,
            "tags": ["bug"],
            "due_date": None,
            "assignees": ["alice"],
            "parent": None,
        }
    ]


async def test_get_tasks_with_statuses(mock_api):
    from urllib.parse import parse_qs, urlparse

    route = mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"tasks": []})
    )
    await get_tasks("l1", statuses=["todo", "done"])
    parsed = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert parsed["statuses[]"] == ["todo", "done"]


# ── pagination (#7) ──────────────────────────────────────────────────


async def test_get_all_tasks_has_more(mock_api):
    mock_api.get("/list/l1/task").mock(
        side_effect=[
            httpx.Response(200, json={"tasks": [mock_task(id="a")], "has_more": True}),
            httpx.Response(200, json={"tasks": [mock_task(id="b")], "has_more": False}),
        ]
    )
    res = await get_tasks("l1", auto_paginate=True)
    assert [t["id"] for t in res] == ["a", "b"]


async def test_get_all_tasks_short_page(mock_api):
    page = [mock_task(id=str(i)) for i in range(50)]  # < 100 => stop
    mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"tasks": page})
    )
    res = await get_tasks("l1", auto_paginate=True)
    assert len(res) == 50


async def test_get_all_pages_cap(mock_api, monkeypatch):
    # Cap reached without a short page / has_more signal.
    monkeypatch.setattr("clickup_mcp.tools.tasks._MAX_PAGES", 1)
    page = [mock_task(id=str(i)) for i in range(100)]
    mock_api.get("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"tasks": page})
    )
    res = await get_tasks("l1", auto_paginate=True)
    assert len(res) == 100


# ── get_task ──────────────────────────────────────────────────────────


async def test_get_task(mock_api):
    mock_api.get("/task/t1").mock(
        return_value=httpx.Response(
            200,
            json=mock_task(
                id="t1",
                name="T",
                status="open",
                tags=["bug"],
                assignees=["alice"],
                text_content="desc",
                subtasks=[{"id": "s1", "name": "Sub", "status": {"status": "open"}}],
            ),
        )
    )
    res = await get_task("t1")
    assert res["id"] == "t1"
    assert res["description"] == "desc"
    assert res["tags"] == ["bug"]
    assert res["assignees"] == ["alice"]
    assert res["subtasks"] == [{"id": "s1", "name": "Sub", "status": "open"}]


# ── create_task (#11 pydantic + #12 dates) ───────────────────────────


async def test_create_task_iso_due_date(mock_api):
    route = mock_api.post("/list/l1/task").mock(
        return_value=httpx.Response(200, json={"id": "t1", "name": "T", "url": "u"})
    )
    res = await create_task(
        "l1", "T", due_date="2026-08-15T09:00:00Z", tags=["bug"], assignees=[1]
    )
    assert res == {"id": "t1", "custom_id": None, "name": "T", "url": "u"}
    body = json.loads(route.calls[0].request.content)
    assert body["due_date"] == 1786784400000
    assert body["tags"] == ["bug"]
    assert body["assignees"] == [1]


# ── create_task_with_subtasks (#5 partial failure) ───────────────────


async def test_create_with_subtasks_success(mock_api):
    mock_api.post("/list/l1/task").mock(
        side_effect=[
            httpx.Response(200, json={"id": "p", "name": "Parent", "url": "pu"}),
            httpx.Response(200, json={"id": "s1", "name": "A", "url": "su1"}),
            httpx.Response(200, json={"id": "s2", "name": "B", "url": "su2"}),
        ]
    )
    res = await create_task_with_subtasks("l1", "Parent", ["A", "B"])
    assert res["id"] == "p"
    assert res["subtasks"] == [
        {"id": "s1", "custom_id": None, "name": "A"},
        {"id": "s2", "custom_id": None, "name": "B"},
    ]
    assert "partial" not in res
    bodies = [json.loads(c.request.content) for c in mock_api.calls]
    assert bodies[1] == {"name": "A", "parent": "p"}
    assert bodies[2] == {"name": "B", "parent": "p"}


async def test_create_with_subtasks_partial(mock_api):
    mock_api.post("/list/l1/task").mock(
        side_effect=[
            httpx.Response(200, json={"id": "p", "name": "Parent", "url": "pu"}),
            httpx.Response(200, json={"id": "s1", "name": "A", "url": "su1"}),
            httpx.Response(404, json={"err": "nope", "ECODE": 404}),
        ]
    )
    res = await create_task_with_subtasks("l1", "Parent", ["A", "B"])
    assert res["partial"] is True
    assert res["subtasks"] == [{"id": "s1", "custom_id": None, "name": "A"}]
    assert "nope" in res["error"]


# ── update_task ──────────────────────────────────────────────────────


async def test_update_task(mock_api):
    route = mock_api.put("/task/t1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "t1", "name": "T", "status": {"status": "done"}, "url": "u"},
        )
    )
    res = await update_task("t1", status="done", due_date="2026-08-15T09:00:00Z")
    assert res["status"] == "done"
    body = json.loads(route.calls[0].request.content)
    assert body == {"status": "done", "due_date": 1786784400000}


async def test_update_task_no_fields(mock_api):
    route = mock_api.put("/task/t1").mock(
        return_value=httpx.Response(
            200, json={"id": "t1", "name": "T", "status": {"status": "open"}, "url": "u"}
        )
    )
    res = await update_task("t1")
    assert res["name"] == "T"
    body = json.loads(route.calls[0].request.content)
    assert body == {}


# ── update_task_status ───────────────────────────────────────────────


async def test_update_task_status(mock_api):
    route = mock_api.put("/task/t1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "t1",
                "custom_id": "CU-1",
                "name": "T",
                "status": {"status": "in progress"},
            },
        )
    )
    res = await update_task_status("t1", "in progress")
    assert res == {"id": "t1", "custom_id": "CU-1", "name": "T", "status": "in progress"}
    body = json.loads(route.calls[0].request.content)
    assert body == {"status": "in progress"}


# ── delete_task (#9 distinguishes not found) ─────────────────────────


async def test_delete_task(mock_api):
    mock_api.delete("/task/t1").mock(return_value=httpx.Response(204))
    assert await delete_task("t1") == {"deleted": True, "task_id": "t1"}


async def test_delete_task_not_found(mock_api):
    mock_api.delete("/task/missing").mock(
        return_value=httpx.Response(404, json={"err": "Task not found", "ECODE": 404})
    )
    with pytest.raises(ClickUpError):
        await delete_task("missing")

