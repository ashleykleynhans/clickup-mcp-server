#!/usr/bin/env python3
"""ClickUp MCP Server - Manage ClickUp tasks from an MCP client.

Thin entry point: the real implementation lives in the :mod:`clickup_mcp`
package. Kept as a module so the ``clickup-mcp-server`` console script and the
documented ``python server.py`` invocation both keep working.
"""

from clickup_mcp import main  # noqa: F401  (re-exported for entry point)

if __name__ == "__main__":  # pragma: no cover
    main()
