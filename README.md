# ClickUp MCP Server

An MCP (Model Context Protocol) server that lets you manage ClickUp tasks directly from Claude Code.

## Features

- **Workspace navigation** — list workspaces, spaces, folders, and lists
- **Task management** — create, read, update, delete tasks
- **Subtasks** — create tasks with subtasks in one operation, or add subtasks individually
- **Status management** — update task and subtask statuses
- **Tags** — list, add, and remove tags
- **Checklists** — create checklists and checklist items on tasks
- **Comments** — read and add comments
- **Search** — search tasks across a workspace

## 20 Tools

| Category   | Tools                                                                                                                   |
|------------|-------------------------------------------------------------------------------------------------------------------------|
| Hierarchy  | `get_workspaces`, `get_spaces`, `get_folders`, `get_lists`, `get_folderless_lists`                                      |
| Tasks      | `get_tasks`, `get_task`, `create_task`, `create_task_with_subtasks`, `update_task`, `update_task_status`, `delete_task` |
| Tags       | `get_space_tags`, `add_tag_to_task`, `remove_tag_from_task`                                                             |
| Checklists | `create_checklist`, `create_checklist_item`                                                                             |
| Comments   | `get_task_comments`, `add_comment`                                                                                      |
| Search     | `search_tasks`                                                                                                          |

## Setup

### 1. Clone and install

```bash
cd /path/to/clickup-mcp-server
python3.12 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Configure your API token

Get a personal API token from ClickUp: **Settings > Apps > API Token**

```bash
cp .env.example .env
# Edit .env and add your token
```

### 3. Add to Claude Code

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

## Usage examples

- "List my ClickUp workspaces"
- "Show me all tasks in list 12345"
- "Create a task called 'Fix login bug' with tags 'bug' and 'urgent' in list 12345"
- "Create a task 'Launch feature' with subtasks 'Write docs', 'Update tests', 'Deploy'"
- "Update task abc123 status to 'in progress'"
- "Search for tasks matching 'onboarding'"

## Requirements

- Python 3.12+
- ClickUp personal API token
