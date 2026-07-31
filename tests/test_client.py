import httpx
import pytest

from clickup_mcp import client
from clickup_mcp.client import (
    _backoff_delay,
    _status_error,
    close_client,
    get_client,
    request,
)
from clickup_mcp.errors import ClickUpError


# ── client lifecycle / headers ──────────────────────────────────────


async def test_get_client_singleton():
    await close_client()  # start fresh
    a = get_client()
    b = get_client()
    assert a is b
    await close_client()


async def test_close_client_idempotent():
    get_client()  # _client now set
    await close_client()  # closes (True branch)
    assert client._client is None
    await close_client()  # _client already None -> no-op branch
    assert client._client is None


async def test_headers_only_authorization():
    await close_client()
    h = client._headers()
    assert "Authorization" in h
    # Content-Type must NOT be pinned at client level (multipart uploads rely
    # on httpx setting it per request).
    assert "Content-Type" not in h


async def test_authorization_header_actually_sent(mock_api):
    await close_client()
    monkeypatch_token = "tok-123"
    client.API_TOKEN = monkeypatch_token
    try:
        mock_api.get("/x").mock(return_value=httpx.Response(200, json={"ok": True}))
        await request("GET", "/x")
        sent = mock_api.calls[0].request.headers["Authorization"]
        assert sent == monkeypatch_token
    finally:
        client.API_TOKEN = ""
        await close_client()


# ── request: happy paths ────────────────────────────────────────────


async def test_request_json(mock_api):
    mock_api.get("/test").mock(return_value=httpx.Response(200, json={"ok": True}))
    assert await request("GET", "/test") == {"ok": True}


async def test_request_204(mock_api):
    mock_api.delete("/gone").mock(return_value=httpx.Response(204))
    assert await request("DELETE", "/gone") == {}


async def test_request_empty_body(mock_api):
    mock_api.post("/empty").mock(return_value=httpx.Response(200, content=b""))
    assert await request("POST", "/empty") == {}


# ── request: error surfacing (#2) ───────────────────────────────────


async def test_request_surfaces_api_error_json(mock_api):
    mock_api.get("/missing").mock(
        return_value=httpx.Response(
            404, json={"err": "Task not found", "ECODE": 404}
        )
    )
    with pytest.raises(ClickUpError) as exc_info:
        await request("GET", "/missing")
    assert exc_info.value.status_code == 404
    assert "Task not found" in str(exc_info.value)
    assert "404" in str(exc_info.value)


async def test_request_surfaces_api_error_non_json(mock_api):
    mock_api.get("/bad").mock(return_value=httpx.Response(400, content=b"plain text"))
    with pytest.raises(ClickUpError) as exc_info:
        await request("GET", "/bad")
    assert exc_info.value.status_code == 400
    assert "plain text" in str(exc_info.value)


# ── _status_error unit ──────────────────────────────────────────────


def test_status_error_json_with_ecode():
    resp = httpx.Response(500, json={"err": "boom", "ECODE": 500})
    err = _status_error(resp)
    assert err.status_code == 500
    msg = str(err)
    assert "500" in msg
    assert "boom" in msg


def test_status_error_non_json():
    resp = httpx.Response(400, content=b"oops")
    err = _status_error(resp)
    assert err.status_code == 400
    assert "oops" in str(err)


# ── retry: 429 / 5xx / transport errors (#4) ────────────────────────


async def test_retry_429_then_success(mock_api, no_sleep):
    mock_api.get("/r").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    assert await request("GET", "/r") == {"ok": True}
    assert no_sleep  # slept once between attempts


async def test_retry_429_invalid_retry_after(mock_api, no_sleep):
    # Retry-After is non-numeric -> fall back to exponential backoff.
    mock_api.get("/r").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "soon"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    assert await request("GET", "/r") == {"ok": True}
    assert no_sleep == [0.4]  # _BASE_BACKOFF * 2**0


async def test_retry_exhausted_on_429(mock_api, no_sleep):
    mock_api.get("/r").mock(return_value=httpx.Response(429))
    with pytest.raises(ClickUpError) as exc_info:
        await request("GET", "/r")
    assert exc_info.value.status_code == 429


async def test_retry_transport_error_then_success(mock_api, no_sleep):
    mock_api.get("/r").mock(
        side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json={"ok": True})]
    )
    assert await request("GET", "/r") == {"ok": True}
    assert no_sleep  # retried after the transport error


async def test_retry_transport_error_exhausted(mock_api, no_sleep):
    mock_api.get("/r").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(ClickUpError) as exc_info:
        await request("GET", "/r")
    assert "transport error" in str(exc_info.value).lower()


# ── _backoff_delay unit ─────────────────────────────────────────────


def test_backoff_exponential():
    assert _backoff_delay(0, None) == 0.4
    assert _backoff_delay(1, None) == 0.8
    assert _backoff_delay(2, None) == 1.6


def test_backoff_retry_after_numeric():
    assert _backoff_delay(0, "2") == 2.0


def test_backoff_retry_after_invalid():
    assert _backoff_delay(0, "soon") == 0.4
