import importlib

import dotenv


def test_client_loads_dotenv_on_import(monkeypatch):
    """Regression: client.py must call load_dotenv() so a token placed in a
    .env file is picked up even when the spawning process (e.g. Claude Code)
    doesn't already export CLICKUP_API_TOKEN in the environment."""
    called = {"n": 0}

    def fake_load_dotenv(*args, **kwargs):
        called["n"] += 1

    monkeypatch.setattr(dotenv, "load_dotenv", fake_load_dotenv)
    import clickup_mcp.client as client

    importlib.reload(client)
    try:
        assert called["n"] == 1
    finally:
        # Restore the real load_dotenv binding inside the module.
        monkeypatch.undo()
        importlib.reload(client)
