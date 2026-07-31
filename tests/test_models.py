import pytest
from pydantic import ValidationError

from clickup_mcp.models import TaskCreate, TaskUpdate


def test_task_create_date_coercion_iso():
    body = TaskCreate(name="t", due_date="2026-08-15T09:00:00Z").model_dump(exclude_none=True)
    assert body["due_date"] == 1786784400000
    assert body["name"] == "t"


def test_task_create_date_coercion_int():
    body = TaskCreate(name="t", due_date=1700000000000).model_dump(exclude_none=True)
    assert body["due_date"] == 1700000000000


def test_task_create_start_date_coercion():
    body = TaskCreate(name="t", start_date="2026-08-15T09:00:00Z").model_dump(exclude_none=True)
    assert body["start_date"] == 1786784400000


def test_task_create_excludes_none():
    body = TaskCreate(name="t").model_dump(exclude_none=True)
    assert body == {"name": "t"}


def test_task_create_invalid_date_raises():
    with pytest.raises(ValidationError):
        TaskCreate(name="t", due_date="not-a-date")


def test_task_update_excludes_unset():
    body = TaskUpdate(status="done", due_date="2026-08-15T09:00:00Z").model_dump(exclude_none=True)
    assert body == {"status": "done", "due_date": 1786784400000}


def test_task_update_all_none_is_empty():
    body = TaskUpdate().model_dump(exclude_none=True)
    assert body == {}


def test_task_update_date_coercion():
    body = TaskUpdate(due_date="2026-08-15T09:00:00Z").model_dump(exclude_none=True)
    assert body["due_date"] == 1786784400000
