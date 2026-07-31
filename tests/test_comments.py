import httpx

from clickup_mcp.tools.comments import add_comment, get_task_comments


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
    res = await get_task_comments("t1")
    assert len(res) == 1
    assert res[0]["text"] == "hello"
    assert res[0]["user"] == "alice"


async def test_add_comment(mock_api):
    mock_api.post("/task/t1/comment").mock(
        return_value=httpx.Response(200, json={"id": "c2", "hist_id": "h1"})
    )
    assert await add_comment("t1", "my comment") == {"id": "c2", "hist_id": "h1"}
