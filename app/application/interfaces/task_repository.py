"""Application Port: Task Repository — abstract contract for task persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Task


class ITaskRepository(ABC):
    """Interface that any task persistence adapter must implement.

    Defined in the Application layer so use cases depend on this abstraction,
    never on a concrete database implementation.
    """

    @abstractmethod
    async def get_by_id(self, task_id: UUID) -> Task | None:
        """Retrieve a single task by its unique identifier."""

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> list[Task]:
        """Retrieve all tasks belonging to a specific user."""

    @abstractmethod
    async def create(self, task: Task) -> Task:
        """Persist a new task and return the stored representation."""

    @abstractmethod
    async def update(self, task: Task) -> Task:
        """Update an existing task and return the stored representation."""

    @abstractmethod
    async def delete(self, task_id: UUID) -> None:
        """Remove a task by its unique identifier."""
