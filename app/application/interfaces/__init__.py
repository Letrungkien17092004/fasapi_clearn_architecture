"""Application interfaces — abstract ports for infrastructure adapters."""

from app.application.interfaces.auth_service import IAuthService
from app.application.interfaces.task_repository import ITaskRepository

__all__ = ["IAuthService", "ITaskRepository"]
