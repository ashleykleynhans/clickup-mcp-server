from clickup_mcp import create_mcp


def test_create_mcp_registers_all_tools():
    mcp = create_mcp()
    # 21 original + 17 new = 38 tools.
    import asyncio

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    # Spot-check a representative tool from every category.
    expected = {
        "get_workspaces",
        "create_space",
        "create_task",
        "create_task_with_subtasks",
        "get_checklists",
        "update_checklist_item",
        "delete_checklist",
        "get_time_entries",
        "start_timer",
        "stop_timer",
        "get_list_custom_fields",
        "set_task_custom_field",
        "get_attachments",
        "add_attachment",
        "search_tasks",
    }
    assert expected <= names, expected - names
    assert len(tools) == 38
