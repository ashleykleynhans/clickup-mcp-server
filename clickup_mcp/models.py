"""Pydantic models for task create/update payloads.

Using models (instead of hand-built dicts) gives validation, type safety and
``model_dump(exclude_none=True)`` so only provided fields are sent - which also
keeps the create / update field lists in sync.
"""

from pydantic import BaseModel, field_validator

from .dates import parse_datetime_to_ms


class _TaskBase(BaseModel):
    """Fields shared by task create & update payloads."""

    description: str | None = None
    markdown_content: str | None = None
    status: str | None = None
    priority: int | None = None
    due_date: int | str | None = None
    start_date: int | str | None = None
    time_estimate: int | None = None
    parent: str | None = None

    @field_validator("due_date", "start_date", mode="before")
    @classmethod
    def _coerce_date(cls, value):
        """Allow ISO-8601 strings for due/start dates; ints pass through."""
        if value is None or isinstance(value, int):
            return value
        return parse_datetime_to_ms(value)


class TaskCreate(_TaskBase):
    """Body for ``POST /list/{list_id}/task``."""

    name: str
    tags: list[str] | None = None
    assignees: list[int] | None = None


class TaskUpdate(_TaskBase):
    """Body for ``PUT /task/{task_id}`` (no tags/assignees - use the tag tools)."""

    name: str | None = None
