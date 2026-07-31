import json

import httpx

from clickup_mcp.tools.time_tracking import (
    _curate_entry,
    _first_entry,
    create_time_entry,
    get_current_timer,
    get_time_entries,
    start_timer,
    stop_timer,
)


def _entry(**kw):
    base = {
        "id": "e1",
        "tid": "task1",
        "task": "task1",
        "user": {"username": "alice"},
        "description": "work",
        "billable": True,
        "start": "1000",
        "end": "2000",
        "duration": 1000,
        "tags": [{"name": "dev"}],
        "url": "u",
    }
    base.update(kw)
    return base


# ── _first_entry ─────────────────────────────────────────────────────


def test_first_entry_from_data_list():
    assert _first_entry({"data": [{"id": "x"}]}) == {"id": "x"}


def test_first_entry_empty_data_list():
    assert _first_entry({"data": []}) == {}


def test_first_entry_no_data_key_returns_self():
    entry = {"id": "x", "duration": 5}
    assert _first_entry(entry) == entry


def test_first_entry_non_dict():
    assert _first_entry([]) == {}
    assert _first_entry("nope") == {}


# ── _curate_entry branches ──────────────────────────────────────────


def test_curate_entry_dict_user():
    assert _curate_entry(_entry())["user"] == "alice"


def test_curate_entry_non_dict_user():
    e = _entry(user=42)
    assert _curate_entry(e)["user"] == 42
    # tid present -> used over task
    assert _curate_entry(e)["task"] == "task1"


def test_curate_entry_task_fallback():
    e = _entry()
    e.pop("tid")
    assert _curate_entry(e)["task"] == "task1"


def test_curate_entry_tags_empty_when_none():
    e = _entry()
    e["tags"] = None
    assert _curate_entry(e)["tags"] == []


# ── get_time_entries ─────────────────────────────────────────────────


async def test_get_time_entries_dict(mock_api):
    mock_api.get("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json={"data": [_entry()]})
    )
    res = await get_time_entries("9")
    assert len(res) == 1
    assert res[0]["user"] == "alice"


async def test_get_time_entries_list(mock_api):
    mock_api.get("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json=[_entry()])
    )
    res = await get_time_entries("9")
    assert len(res) == 1


async def test_get_time_entries_filters(mock_api):
    from urllib.parse import parse_qs, urlparse

    route = mock_api.get("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    await get_time_entries(
        "9", start_date="2026-08-15T09:00:00Z", end_date=1700000000000, assignee=[1, 2]
    )
    parsed = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert parsed["start_date"] == ["1786784400000"]
    assert parsed["end_date"] == ["1700000000000"]
    assert parsed["assignee[]"] == ["1", "2"]


# ── get_current_timer ────────────────────────────────────────────────


async def test_get_current_timer_running(mock_api):
    mock_api.get("/team/9/time_entries/current").mock(
        return_value=httpx.Response(
            200, json={"running": True, "data": [_entry()]}
        )
    )
    res = await get_current_timer("9")
    assert res["running"] is True
    assert res["entry"]["task"] == "task1"


async def test_get_current_timer_idle(mock_api):
    mock_api.get("/team/9/time_entries/current").mock(
        return_value=httpx.Response(200, json={"running": False, "data": []})
    )
    res = await get_current_timer("9")
    assert res["running"] is False
    assert res["entry"] is None


async def test_get_current_timer_non_dict(mock_api):
    mock_api.get("/team/9/time_entries/current").mock(
        return_value=httpx.Response(200, json=[])
    )
    res = await get_current_timer("9")
    assert res["running"] is False
    assert res["entry"] is None


# ── create_time_entry ────────────────────────────────────────────────


async def test_create_time_entry_minimal(mock_api):
    route = mock_api.post("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json={"data": [_entry()]})
    )
    await create_time_entry("9", "task1", "2026-08-15T09:00:00Z", 1000)
    body = json.loads(route.calls[0].request.content)
    assert body == {"tid": "task1", "start": 1786784400000, "duration": 1000, "billable": False}


async def test_create_time_entry_full(mock_api):
    route = mock_api.post("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json={"data": [_entry()]})
    )
    await create_time_entry(
        "9", "task1", 1000, 500, description="d", billable=True, assignee=3, tags=["x"]
    )
    body = json.loads(route.calls[0].request.content)
    assert body == {
        "tid": "task1",
        "start": 1000,
        "duration": 500,
        "billable": True,
        "description": "d",
        "assignee": 3,
        "tags": ["x"],
    }


async def test_create_time_entry_no_data_key(mock_api):
    # Response is the entry itself (no "data" wrapper).
    mock_api.post("/team/9/time_entries").mock(
        return_value=httpx.Response(200, json=_entry())
    )
    res = await create_time_entry("9", "task1", 1000, 500)
    assert res["id"] == "e1"


# ── start_timer / stop_timer ─────────────────────────────────────────


async def test_start_timer(mock_api):
    route = mock_api.post("/team/9/time_entries/start").mock(
        return_value=httpx.Response(200, json={"data": [_entry()]})
    )
    await start_timer("9", "task1", description="d", billable=True, tags=["x"])
    body = json.loads(route.calls[0].request.content)
    assert body == {"tid": "task1", "billable": True, "description": "d", "tags": ["x"]}


async def test_stop_timer(mock_api):
    mock_api.post("/team/9/time_entries/stop").mock(
        return_value=httpx.Response(200, json={"data": [_entry()]})
    )
    res = await stop_timer("9")
    assert res["id"] == "e1"
