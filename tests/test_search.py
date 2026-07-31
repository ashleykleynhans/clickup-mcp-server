import httpx

from clickup_mcp.tools.search import search_tasks
from tests.conftest import mock_task


async def test_search_tasks(mock_api):
    mock_api.get("/team/1/task").mock(
        return_value=httpx.Response(200, json={"tasks": [mock_task(list_name="My List")]})
    )
    res = await search_tasks("1", "test")
    assert len(res) == 1
    assert res[0]["custom_id"] == "CU-1"
    assert res[0]["list"] == "My List"
