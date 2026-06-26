"""Domain layer — entities and business exceptions."""

from app.domain.entities import Task, TaskStatus, User
from app.domain.exceptions import (
    AuthenticationError,
    DomainError,
    TaskNotFoundError,
    TaskPermissionError,
)

__all__ = [
    "AuthenticationError",
    "DomainError",
    "Task",
    "TaskNotFoundError",
    "TaskPermissionError",
    "TaskStatus",
    "User",
]
