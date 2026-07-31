import json

import httpx

from clickup_mcp.tools.checklists import (
    create_checklist,
    create_checklist_item,
    delete_checklist,
    delete_checklist_item,
    get_checklists,
    update_checklist_item,
)


async def test_create_checklist(mock_api):
    mock_api.post("/task/t1/checklist").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1", "name": "Todo"}})
    )
    assert await create_checklist("t1", "Todo") == {"id": "cl1", "name": "Todo"}


async def test_get_checklists(mock_api):
    mock_api.get("/task/t1/checklist").mock(
        return_value=httpx.Response(
            200,
            json={
                "checklists": [
                    {
                        "id": "cl1",
                        "name": "Todo",
                        "resolved": False,
                        "items": [
                            {"id": "i1", "name": "A", "resolved": True, "assignee": 5},
                            {"id": "i2", "name": "B", "resolved": False, "assignee": None},
                        ],
                    }
                ]
            },
        )
    )
    res = await get_checklists("t1")
    assert res == [
        {
            "id": "cl1",
            "name": "Todo",
            "resolved": False,
            "items": [
                {"id": "i1", "name": "A", "resolved": True, "assignee": 5},
                {"id": "i2", "name": "B", "resolved": False, "assignee": None},
            ],
        }
    ]


async def test_create_checklist_item_no_assignee(mock_api):
    mock_api.post("/checklist/cl1/checklist_item").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1", "items": []}})
    )
    res = await create_checklist_item("cl1", "Item 1")
    assert "id" in res


async def test_create_checklist_item_with_assignee(mock_api):
    route = mock_api.post("/checklist/cl1/checklist_item").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1"}})
    )
    await create_checklist_item("cl1", "Item 2", assignee=42)
    assert json.loads(route.calls[0].request.content) == {"name": "Item 2", "assignee": 42}


async def test_update_checklist_item_all_fields(mock_api):
    route = mock_api.put("/checklist/cl1/checklist_item/i1").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1"}})
    )
    await update_checklist_item(
        "cl1", "i1", name="X", resolved=True, assignee=9, due_date="2026-08-15T09:00:00Z"
    )
    body = json.loads(route.calls[0].request.content)
    assert body == {"name": "X", "resolved": True, "assignee": 9, "due_date": 1786784400000}


async def test_update_checklist_item_one_field(mock_api):
    route = mock_api.put("/checklist/cl1/checklist_item/i1").mock(
        return_value=httpx.Response(200, json={"checklist": {"id": "cl1"}})
    )
    await update_checklist_item("cl1", "i1", resolved=False)
    assert json.loads(route.calls[0].request.content) == {"resolved": False}


async def test_delete_checklist_item(mock_api):
    mock_api.delete("/checklist/cl1/checklist_item/i1").mock(
        return_value=httpx.Response(200, json={})
    )
    assert await delete_checklist_item("cl1", "i1") == {
        "deleted": True,
        "checklist_item_id": "i1",
    }


async def test_delete_checklist(mock_api):
    mock_api.delete("/checklist/cl1").mock(return_value=httpx.Response(200, json={}))
    assert await delete_checklist("cl1") == {"deleted": True, "checklist_id": "cl1"}
