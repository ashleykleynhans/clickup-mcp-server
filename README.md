# ClickUp MCP Server

An MCP (Model Context Protocol) server that lets you manage ClickUp tasks directly from Claude Code (or any MCP client).

## Features

- **Workspace navigation** — list workspaces, members, spaces, folders, and lists; create spaces / folders / lists
- **Task management** — create, read, update, delete tasks; partial-failure reporting for batch subtask creation
- **Pagination** — fetch a single page or auto-paginate through every task in a list
- **Subtasks** — create tasks with subtasks in one operation, or add subtasks individually
- **Status management** — update task and subtask statuses
- **Tags** — list, add, and remove tags
- **Checklists** — create, list, update, and delete checklists and checklist items
- **Comments** — read and add comments
- **Time tracking** — list entries, get the running timer, log entries, start / stop the timer
- **Custom fields** — list fields and set values on tasks
- **Attachments** — list and upload file attachments
- **Search** — search tasks across a workspace
- **Reliability** — pooled connections, automatic retry with backoff on 429 / 5xx, and real API error surfacing
- **Flexible transports** — run over stdio (default), SSE, or streamable HTTP

## 38 Tools

| Category        | Tools                                                                                                                                                                                              |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Hierarchy       | `get_workspaces`, `get_members`, `get_spaces`, `get_folders`, `get_lists`, `get_folderless_lists`, `create_space`, `create_folder`, `create_list`, `create_folderless_list`                        |
| Tasks           | `get_tasks`, `get_task`, `create_task`, `create_task_with_subtasks`, `update_task`, `update_task_status`, `delete_task`                                                                            |
| Tags            | `get_space_tags`, `add_tag_to_task`, `remove_tag_from_task`                                                                                                                                         |
| Checklists      | `create_checklist`, `get_checklists`, `create_checklist_item`, `update_checklist_item`, `delete_checklist_item`, `delete_checklist`                                                                |
| Comments        | `get_task_comments`, `add_comment`                                                                                                                                                                  |
| Time tracking   | `get_time_entries`, `get_current_timer`, `create_time_entry`, `start_timer`, `stop_timer`                                                                                                          |
| Custom fields   | `get_list_custom_fields`, `set_task_custom_field`                                                                                                                                                    |
| Attachments     | `get_attachments`, `add_attachment`                                                                                                                                                                 |
| Search          | `search_tasks`                                                                                                                                                                                       |

## Setup

### 1. Clone and install

```bash
cd /path/to/clickup-mcp-server
python3.12 -m venv .venv
.venv/bin/pip install -e ".[test]"   # drop [test] if you don't need the test suite
```

### 2. Configure your API token

Get a personal API token from ClickUp: **Settings > Apps > API Token**

```bash
cp .env.example .env
# Edit .env and add your token
```

The server **fails fast** at startup if `CLICKUP_API_TOKEN` is missing, rather than failing opaquely on every request.

### 3. Add to Claude Code (stdio)

```bash
claude mcp add --scope user -t stdio clickup -- \
  /path/to/clickup-mcp-server/.venv/bin/python \
  /path/to/clickup-mcp-server/server.py
```

Or manually add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "clickup": {
      "type": "stdio",
      "command": "/path/to/clickup-mcp-server/.venv/bin/python",
      "args": ["/path/to/clickup-mcp-server/server.py"]
    }
  }
}
```

### 4. Restart Claude Code

The ClickUp tools will be available automatically in all sessions.

## Transports (optional)

The default transport is **stdio**. Set `CLICKUP_MCP_TRANSPORT` to run the server over the network instead:

| Transport         | Env value            | Use case                                  |
|-------------------|----------------------|-------------------------------------------|
| Standard I/O      | `stdio` (default)    | Local clients like Claude Code            |
| SSE               | `sse`                | Remote / agent-hosted deployments         |
| Streamable HTTP   | `streamable-http`    | Remote / agent-hosted deployments         |

## Configuration reference

| Variable                  | Default     | Description                                                       |
|---------------------------|-------------|-------------------------------------------------------------------|
| `CLICKUP_API_TOKEN`       | —           | Your ClickUp personal API token (required).                       |
| `CLICKUP_MCP_TRANSPORT`   | `stdio`     | One of `stdio`, `sse`, `streamable-http`.                         |
| `CLICKUP_MCP_LOG_LEVEL`   | `WARNING`   | Stderr log level (`DEBUG`, `INFO`, `WARNING`, …).                 |

## Notes for LLM-friendly inputs

- **Dates** — `due_date` and `start_date` accept either a Unix timestamp in **milliseconds** (`1786784400000`) or an **ISO-8601** string (`"2026-08-15T09:00:00Z"`). Naive datetimes are interpreted as UTC.
- **`time_estimate`** is a duration in milliseconds (not a timestamp).
- **Assignees** expect numeric user IDs — use `get_members` to resolve a person's name to their ID.
- **Errors** surface the ClickUp API's own message and `ECODE` (e.g. `ClickUp API 404 (404): Task not found`) so problems are easy to diagnose.

## Usage examples

- "List my ClickUp workspaces"
- "Show me all tasks in list 12345" (single page) / "… every task in list 12345" (auto-paginate)
- "Create a task called 'Fix login bug' with tags 'bug' and 'urgent' in list 12345, due 2026-08-15"
- "Create a task 'Launch feature' with subtasks 'Write docs', 'Update tests', 'Deploy'"
- "Update task abc123 status to 'in progress'"
- "Mark checklist item complete on task abc123"
- "Start the timer on task abc123"
- "Search for tasks matching 'onboarding'"

## Development

```bash
.venv/bin/pip install -e ".[test]"
.venv/bin/pytest -v          # 100% coverage is enforced (--cov-fail-under=100)
```

The implementation lives in the `clickup_mcp` package; `server.py` is a thin entry
point kept so the documented `python server.py` and `clickup-mcp-server`
invocations keep working.

## Requirements

- Python 3.12+
- ClickUp personal API token
