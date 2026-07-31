import httpx

from clickup_mcp.tools.tags import add_tag_to_task, get_space_tags, remove_tag_from_task


async def test_get_space_tags(mock_api):
    mock_api.get("/space/s1/tag").mock(
        return_value=httpx.Response(
            200, json={"tags": [{"name": "bug", "tag_fg": "#fff", "tag_bg": "#f00"}]}
        )
    )
    assert await get_space_tags("s1") == [
        {"name": "bug", "fg_color": "#fff", "bg_color": "#f00"}
    ]


async def test_add_tag_to_task(mock_api):
    mock_api.post("/task/t1/tag/bug").mock(return_value=httpx.Response(200, json={}))
    assert await add_tag_to_task("t1", "bug") == {"task_id": "t1", "tag_added": "bug"}


async def test_remove_tag_from_task(mock_api):
    mock_api.delete("/task/t1/tag/bug").mock(return_value=httpx.Response(200, json={}))
    assert await remove_tag_from_task("t1", "bug") == {
        "task_id": "t1",
        "tag_removed": "bug",
    }
