import httpx
import pytest
import respx

from server import CLICKUP_API


@pytest.fixture()
def mock_api():
    with respx.mock(base_url=CLICKUP_API) as api:
        yield api


def mock_task(
    id="task1",
    custom_id="CU-1",
    name="Test Task",
    status="open",
    priority=None,
    tags=None,
    due_date=None,
    start_date=None,
    time_estimate=None,
    assignees=None,
    parent=None,
    subtasks=None,
    text_content=None,
    url="https://app.clickup.com/t/task1",
    list_name=None,
):
    t = {
        "id": id,
        "custom_id": custom_id,
        "name": name,
        "status": {"status": status},
        "priority": priority,
        "tags": [{"name": n} for n in (tags or [])],
        "due_date": due_date,
        "start_date": start_date,
        "time_estimate": time_estimate,
        "assignees": [{"username": u} for u in (assignees or [])],
        "parent": parent,
        "subtasks": subtasks or [],
        "text_content": text_content,
        "url": url,
    }
    if list_name is not None:
        t["list"] = {"name": list_name}
    return t
