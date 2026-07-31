"""Custom exceptions for the ClickUp MCP server."""


class ClickUpError(RuntimeError):
    """Raised when the ClickUp API returns an error or a request fails.

    Carries the HTTP ``status_code`` when available so callers can distinguish
    not-found (404), auth (401) and rate-limit (429) situations.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
