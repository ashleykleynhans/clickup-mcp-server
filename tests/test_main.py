import logging

import pytest

import clickup_mcp
from clickup_mcp import main
from clickup_mcp.errors import ClickUpError


class _FakeMCP:
    def __init__(self):
        self.transport = None

    def run(self, transport=None, mount_path=None):
        self.transport = transport


def _set_token(monkeypatch, value):
    monkeypatch.setattr("clickup_mcp.API_TOKEN", value)


def test_server_entry_reexports_main():
    import server

    assert callable(server.main)


def test_main_runs_stdio(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.delenv("CLICKUP_MCP_TRANSPORT", raising=False)
    fake = _FakeMCP()
    monkeypatch.setattr("clickup_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "stdio"


def test_main_runs_sse(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("CLICKUP_MCP_TRANSPORT", "sse")
    fake = _FakeMCP()
    monkeypatch.setattr("clickup_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "sse"


def test_main_runs_streamable_http(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("CLICKUP_MCP_TRANSPORT", "streamable-http")
    fake = _FakeMCP()
    monkeypatch.setattr("clickup_mcp.create_mcp", lambda: fake)
    main()
    assert fake.transport == "streamable-http"


def test_main_missing_token_raises(monkeypatch):
    _set_token(monkeypatch, "")
    monkeypatch.delenv("CLICKUP_API_TOKEN", raising=False)
    with pytest.raises(ClickUpError):
        main()


def test_main_invalid_transport_raises(monkeypatch):
    _set_token(monkeypatch, "tok")
    monkeypatch.setenv("CLICKUP_MCP_TRANSPORT", "bogus")
    with pytest.raises(ClickUpError):
        main()


def test_main_configures_logging_once(monkeypatch):
    # Calling main twice: handler is added on the first call and skipped on
    # the second (covers the "if not logger.handlers" both branches).
    _set_token(monkeypatch, "tok")
    monkeypatch.delenv("CLICKUP_MCP_TRANSPORT", raising=False)
    fake = _FakeMCP()
    monkeypatch.setattr("clickup_mcp.create_mcp", lambda: fake)
    logger = logging.getLogger("clickup_mcp")
    logger.handlers.clear()
    main()
    assert logger.handlers
    main()
    assert len(logger.handlers) == 1


def test_configure_logging_invalid_level(monkeypatch):
    monkeypatch.setenv("CLICKUP_MCP_LOG_LEVEL", "Bogus")
    logger = logging.getLogger("clickup_mcp")
    logger.handlers.clear()
    clickup_mcp._configure_logging()
    assert logger.level == logging.WARNING
