"""Infrastructure repositories — concrete persistence adapters."""

from app.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository

__all__ = ["SQLAlchemyTaskRepository"]
