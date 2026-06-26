"""Pydantic schemas for the /tasks API endpoints.

These live in the Presentation layer only — the Domain and Application
layers use pure dataclasses and never import Pydantic.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities import TaskStatus


# ── Request schemas ────────────────────────────────────────────────


class TaskCreateRequest(BaseModel):
    """Body for POST /tasks."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)


class TaskUpdateRequest(BaseModel):
    """Body for PATCH /tasks/{task_id}."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None


# ── Response schemas ───────────────────────────────────────────────


class TaskResponse(BaseModel):
    """Single task representation returned to the client."""

    id: UUID
    title: str
    description: str
    status: TaskStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Envelope for a list of tasks."""

    tasks: list[TaskResponse]
    count: int
