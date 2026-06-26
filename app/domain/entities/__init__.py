"""Domain entities — pure Python dataclasses."""

from app.domain.entities.task import Task, TaskStatus
from app.domain.entities.user import User

__all__ = ["Task", "TaskStatus", "User"]
