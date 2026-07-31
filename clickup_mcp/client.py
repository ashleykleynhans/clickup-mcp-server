"""Shared HTTP client for the ClickUp v2 API.

A single ``httpx.AsyncClient`` is reused across requests (connection pooling),
transient failures (429 / 5xx / transport errors) are retried with backoff, and
real API error bodies are surfaced instead of being swallowed.
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from .errors import ClickUpError

CLICKUP_API = "https://api.clickup.com/api/v2"
API_TOKEN = os.getenv("CLICKUP_API_TOKEN", "")

logger = logging.getLogger("clickup_mcp")

# Status codes worth retrying.
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BASE_BACKOFF = 0.4  # seconds; doubled per attempt

# Indirection so tests can patch the sleep without touching the global asyncio.
_async_sleep = asyncio.sleep

_client: httpx.AsyncClient | None = None


def _headers() -> dict[str, str]:
    """Authorization header only.

    httpx sets ``Content-Type`` per request (json -> application/json,
    files -> multipart/form-data), so we must NOT pin it at the client level or
    multipart uploads would be sent as application/json.
    """
    return {"Authorization": API_TOKEN}


def get_client() -> httpx.AsyncClient:
    """Return the process-wide, lazily-created async client (pooled connections)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(headers=_headers(), timeout=30)
    return _client


async def close_client() -> None:
    """Close the shared client. Safe to call multiple times; mainly for tests."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _backoff_delay(attempt: int, retry_after: str | None) -> float:
    """Compute the sleep before the next retry attempt."""
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass  # fall through to exponential backoff
    return _BASE_BACKOFF * (2 ** attempt)


def _status_error(resp: httpx.Response) -> ClickUpError:
    """Build a ClickUpError carrying the API's own error message when present."""
    try:
        body = resp.json()
        detail = body.get("err") or body.get("error") or str(body)
        ecode = body.get("ECODE")
    except ValueError:
        detail = resp.text or resp.reason_phrase or ""
        ecode = None
    message = f"ClickUp API {resp.status_code}"
    if ecode:
        message += f" ({ecode})"
    if detail:
        message += f": {detail}"
    return ClickUpError(message, status_code=resp.status_code)


async def _send(method: str, path: str, **kwargs: Any) -> httpx.Response:
    client = get_client()
    url = f"{CLICKUP_API}{path}"
    logger.debug("clickup request %s %s", method, path)
    resp = await client.request(method, url, **kwargs)
    logger.debug("clickup response %s %s -> %s", method, path, resp.status_code)
    return resp


async def request(method: str, path: str, **kwargs: Any) -> dict | list:
    """Perform a ClickUp API request with retry + error surfacing.

    Returns the parsed JSON body (or ``{}`` for empty/204 responses).
    Raises ``ClickUpError`` on HTTP/transport errors.
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = await _send(method, path, **kwargs)
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt == _MAX_RETRIES:
                raise ClickUpError(
                    f"transport error after {_MAX_RETRIES + 1} attempts: {exc}"
                ) from exc
            await _async_sleep(_backoff_delay(attempt, None))
            continue

        if resp.status_code in _RETRYABLE_STATUSES and attempt < _MAX_RETRIES:
            await _async_sleep(_backoff_delay(attempt, resp.headers.get("Retry-After")))
            continue

        # Non-retryable, or the final attempt on a retryable status.
        if resp.status_code >= 400:
            raise _status_error(resp)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    raise ClickUpError(  # pragma: no cover - loop always returns/raises/continues
        f"request failed after {_MAX_RETRIES + 1} attempts: {last_exc}"
    )
