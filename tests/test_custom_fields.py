import json

import httpx

from clickup_mcp.tools.custom_fields import get_list_custom_fields, set_task_custom_field


async def test_get_list_custom_fields(mock_api):
    mock_api.get("/list/l1/field").mock(
        return_value=httpx.Response(
            200,
            json={
                "fields": [
                    {"id": "f1", "name": "Score", "type": "number", "type_config": {}, "date_created": "1"}
                ]
            },
        )
    )
    res = await get_list_custom_fields("l1")
    assert res == [
        {"id": "f1", "name": "Score", "type": "number", "type_config": {}, "date_created": "1"}
    ]


async def test_set_task_custom_field(mock_api):
    route = mock_api.post("/task/t1/field/f1").mock(
        return_value=httpx.Response(200, json={"field": {"id": "f1", "value": 7}})
    )
    res = await set_task_custom_field("t1", "f1", 7)
    assert res == {"id": "f1", "value": 7}
    assert json.loads(route.calls[0].request.content) == {"value": 7}
