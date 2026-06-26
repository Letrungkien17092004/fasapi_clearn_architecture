"""Unit tests for TaskUseCase — pure mock-based, no database or framework.

Demonstrates the power of the Composition Root pattern:
- The use case depends only on ``ITaskRepository`` (an abstract interface).
- We provide a fake in-memory implementation — no SQLAlchemy, no SQLite.
- Tests run fast and verify pure business logic.

Run with:
    pytest tests/test_task_use_case.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.task_use_case import TaskUseCase
from app.domain.entities import Task, TaskStatus
from app.domain.exceptions import TaskNotFoundError, TaskPermissionError


# ── Fake repository ────────────────────────────────────────────────


class InMemoryTaskRepository:
    """In-memory implementation of ``ITaskRepository`` for testing.

    Satisfies the same interface contract without touching a database.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, Task] = {}

    async def get_by_id(self, task_id: UUID) -> Task | None:
        return self._store.get(task_id)

    async def get_by_owner(self, owner_id: UUID) -> list[Task]:
        return [t for t in self._store.values() if t.owner_id == owner_id]

    async def create(self, task: Task) -> Task:
        self._store[task.id] = task
        return task

    async def update(self, task: Task) -> Task:
        self._store[task.id] = task
        return task

    async def delete(self, task_id: UUID) -> None:
        self._store.pop(task_id, None)


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def repo() -> InMemoryTaskRepository:
    """Provide a fresh in-memory repository for each test."""
    return InMemoryTaskRepository()


@pytest.fixture
def use_case(repo: InMemoryTaskRepository) -> TaskUseCase:
    """Provide a use case wired with the fake repository."""
    return TaskUseCase(repo)


@pytest.fixture
def owner_id() -> UUID:
    """A stable owner ID for test isolation."""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def other_user_id() -> UUID:
    """A different user ID for permission tests."""
    return UUID("22222222-2222-2222-2222-222222222222")


# ── Tests ──────────────────────────────────────────────────────────


class TestCreateTask:
    """Tests for TaskUseCase.create_task."""

    @pytest.mark.asyncio
    async def test_creates_task_with_correct_owner(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        task = await use_case.create_task(
            title="Write tests",
            description="Cover all use cases",
            owner_id=owner_id,
        )
        assert task.title == "Write tests"
        assert task.description == "Cover all use cases"
        assert task.owner_id == owner_id
        assert task.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_creates_unique_ids(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        t1 = await use_case.create_task("Task 1", "", owner_id)
        t2 = await use_case.create_task("Task 2", "", owner_id)
        assert t1.id != t2.id


class TestGetTask:
    """Tests for TaskUseCase.get_task."""

    @pytest.mark.asyncio
    async def test_returns_task_when_owner_matches(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        created = await use_case.create_task("Owned task", "", owner_id)
        fetched = await use_case.get_task(created.id, owner_id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_task(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        with pytest.raises(TaskNotFoundError):
            await use_case.get_task(uuid4(), owner_id)

    @pytest.mark.asyncio
    async def test_raises_permission_error_for_wrong_owner(
        self,
        use_case: TaskUseCase,
        owner_id: UUID,
        other_user_id: UUID,
    ) -> None:
        created = await use_case.create_task("Private task", "", owner_id)
        with pytest.raises(TaskPermissionError):
            await use_case.get_task(created.id, other_user_id)


class TestListTasks:
    """Tests for TaskUseCase.list_tasks."""

    @pytest.mark.asyncio
    async def test_returns_only_owner_tasks(
        self,
        use_case: TaskUseCase,
        owner_id: UUID,
        other_user_id: UUID,
    ) -> None:
        await use_case.create_task("My task 1", "", owner_id)
        await use_case.create_task("My task 2", "", owner_id)
        await use_case.create_task("Other task", "", other_user_id)

        tasks = await use_case.list_tasks(owner_id)
        assert len(tasks) == 2
        assert all(t.owner_id == owner_id for t in tasks)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_tasks(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        tasks = await use_case.list_tasks(owner_id)
        assert tasks == []


class TestUpdateTask:
    """Tests for TaskUseCase.update_task."""

    @pytest.mark.asyncio
    async def test_updates_title(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        created = await use_case.create_task("Old title", "desc", owner_id)
        updated = await use_case.update_task(
            created.id, owner_id, title="New title"
        )
        assert updated.title == "New title"
        assert updated.description == "desc"  # unchanged

    @pytest.mark.asyncio
    async def test_updates_status(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        created = await use_case.create_task("Task", "", owner_id)
        updated = await use_case.update_task(
            created.id, owner_id, status=TaskStatus.COMPLETED
        )
        assert updated.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_raises_permission_error_on_update_for_wrong_owner(
        self,
        use_case: TaskUseCase,
        owner_id: UUID,
        other_user_id: UUID,
    ) -> None:
        created = await use_case.create_task("Protected", "", owner_id)
        with pytest.raises(TaskPermissionError):
            await use_case.update_task(created.id, other_user_id, title="Hacked")


class TestDeleteTask:
    """Tests for TaskUseCase.delete_task."""

    @pytest.mark.asyncio
    async def test_deletes_owned_task(
        self, use_case: TaskUseCase, owner_id: UUID
    ) -> None:
        created = await use_case.create_task("To delete", "", owner_id)
        await use_case.delete_task(created.id, owner_id)
        with pytest.raises(TaskNotFoundError):
            await use_case.get_task(created.id, owner_id)

    @pytest.mark.asyncio
    async def test_raises_permission_error_on_delete_for_wrong_owner(
        self,
        use_case: TaskUseCase,
        owner_id: UUID,
        other_user_id: UUID,
    ) -> None:
        created = await use_case.create_task("Not yours", "", owner_id)
        with pytest.raises(TaskPermissionError):
            await use_case.delete_task(created.id, other_user_id)
