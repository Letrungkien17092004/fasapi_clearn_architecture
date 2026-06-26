"""Use Case: Task management — orchestrates domain logic via repository port.

This class lives in the Application layer. It depends ONLY on the
``ITaskRepository`` abstract interface — it has zero knowledge of
SQLAlchemy, FastAPI, or any infrastructure detail.
"""

from uuid import UUID

from app.application.interfaces.task_repository import ITaskRepository
from app.domain.entities import Task, TaskStatus
from app.domain.exceptions import TaskNotFoundError, TaskPermissionError


class TaskUseCase:
    """Application service for task operations.

    The repository is injected via constructor — the Composition Root
    (Presentation layer) decides which concrete implementation to provide.
    """

    def __init__(self, repository: ITaskRepository) -> None:
        self._repository = repository

    async def create_task(
        self,
        title: str,
        description: str,
        owner_id: UUID,
    ) -> Task:
        """Create a new task owned by *owner_id*."""
        task = Task(
            title=title,
            description=description,
            owner_id=owner_id,
        )
        return await self._repository.create(task)

    async def get_task(self, task_id: UUID, owner_id: UUID) -> Task:
        """Fetch a single task, enforcing ownership."""
        task = await self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))
        if task.owner_id != owner_id:
            raise TaskPermissionError(str(owner_id), str(task_id))
        return task

    async def list_tasks(self, owner_id: UUID) -> list[Task]:
        """Return all tasks belonging to *owner_id*."""
        return await self._repository.get_by_owner(owner_id)

    async def update_task(
        self,
        task_id: UUID,
        owner_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
    ) -> Task:
        """Partially update a task, enforcing ownership."""
        task = await self.get_task(task_id, owner_id)  # reuses ownership check
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        return await self._repository.update(task)

    async def delete_task(self, task_id: UUID, owner_id: UUID) -> None:
        """Delete a task, enforcing ownership."""
        await self.get_task(task_id, owner_id)  # reuses ownership check
        await self._repository.delete(task_id)
