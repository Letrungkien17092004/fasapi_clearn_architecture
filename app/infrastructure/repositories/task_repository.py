"""Concrete repository: SQLAlchemy-backed task persistence.

Implements the ``ITaskRepository`` port from the Application layer.
All ORM ↔ Domain mapping happens here — the rest of the app only
sees pure ``Task`` entities.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Task, TaskStatus
from app.infrastructure.models import TaskModel


class SQLAlchemyTaskRepository:
    """Async SQLAlchemy implementation of ITaskRepository.

    Note: This class does **not** inherit from ITaskRepository at runtime
    (to keep Infrastructure free of Application imports), but it satisfies
    the same interface contract. The Composition Root performs the wiring.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── ORM ↔ Domain mapping helpers ────────────────────────────────

    @staticmethod
    def _to_entity(model: TaskModel) -> Task:
        """Map a SQLAlchemy row to a pure domain ``Task``."""
        return Task(
            id=UUID(model.id),
            title=model.title,
            description=model.description,
            status=TaskStatus(model.status),
            owner_id=UUID(model.owner_id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(task: Task) -> TaskModel:
        """Map a domain ``Task`` to a SQLAlchemy model instance."""
        return TaskModel(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status.value,
            owner_id=str(task.owner_id),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    # ── ITaskRepository implementation ──────────────────────────────

    async def get_by_id(self, task_id: UUID) -> Task | None:
        stmt = select(TaskModel).where(TaskModel.id == str(task_id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_owner(self, owner_id: UUID) -> list[Task]:
        stmt = (
            select(TaskModel)
            .where(TaskModel.owner_id == str(owner_id))
            .order_by(TaskModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, task: Task) -> Task:
        model = self._to_model(task)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, task: Task) -> Task:
        stmt = select(TaskModel).where(TaskModel.id == str(task.id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return self._to_entity(model)  # type: ignore[return-value]

        model.title = task.title
        model.description = task.description
        model.status = task.status.value
        model.updated_at = task.updated_at
        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, task_id: UUID) -> None:
        stmt = select(TaskModel).where(TaskModel.id == str(task_id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
