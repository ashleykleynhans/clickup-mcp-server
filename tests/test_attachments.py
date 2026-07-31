import httpx

from clickup_mcp.tools.attachments import add_attachment, get_attachments


async def test_get_attachments(mock_api):
    mock_api.get("/task/t1/attachment").mock(
        return_value=httpx.Response(
            200,
            json={"attachments": [{"id": "a1", "title": "f.txt", "url": "u", "date": "1"}]},
        )
    )
    res = await get_attachments("t1")
    assert res == [{"id": "a1", "title": "f.txt", "url": "u", "date": "1"}]


async def test_add_attachment(mock_api, tmp_path):
    route = mock_api.post("/task/t1/attachment").mock(
        return_value=httpx.Response(
            200, json={"id": "a1", "url": "u", "task_id": "t1", "title": "note.txt"}
        )
    )
    f = tmp_path / "note.txt"
    f.write_bytes(b"hello world")
    res = await add_attachment("t1", str(f))
    assert res == {"id": "a1", "url": "u", "task_id": "t1", "title": "note.txt"}
    # multipart body carries the filename and file contents.
    content_type = route.calls[0].request.headers["content-type"]
    assert "multipart/form-data" in content_type
    assert b"hello world" in route.calls[0].request.content
    assert b"note.txt" in route.calls[0].request.content


async def test_add_attachment_custom_filename(mock_api, tmp_path):
    route = mock_api.post("/task/t1/attachment").mock(
        return_value=httpx.Response(200, json={"id": "a1", "url": "u", "task_id": "t1"})
    )
    f = tmp_path / "note.txt"
    f.write_bytes(b"hi")
    await add_attachment("t1", str(f), filename="renamed.txt")
    assert b"renamed.txt" in route.calls[0].request.content
