"""Presentation layer — /tasks router.

Every endpoint is protected by the JWK auth dependency. The router
never touches the repository or session directly — it receives a
fully-assembled ``TaskUseCase`` via the Composition Root.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.task_use_case import TaskUseCase
from app.domain.entities import User
from app.domain.exceptions import DomainError, TaskNotFoundError, TaskPermissionError
from app.presentation.dependencies.auth_deps import get_current_user
from app.presentation.dependencies.task_deps import get_task_use_case
from app.presentation.schemas.task_schemas import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ── Helpers ────────────────────────────────────────────────────────


def _domain_error_to_http(exc: DomainError) -> HTTPException:
    """Map domain exceptions to the appropriate HTTP status code."""
    if isinstance(exc, TaskNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, TaskPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


# ── Endpoints ──────────────────────────────────────────────────────


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    body: TaskCreateRequest,
    user: User = Depends(get_current_user),
    use_case: TaskUseCase = Depends(get_task_use_case),
) -> TaskResponse:
    """Create a task owned by the authenticated user."""
    task = await use_case.create_task(
        title=body.title,
        description=body.description,
        owner_id=user.id,
    )
    return TaskResponse.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks for the current user",
)
async def list_tasks(
    user: User = Depends(get_current_user),
    use_case: TaskUseCase = Depends(get_task_use_case),
) -> TaskListResponse:
    """Return all tasks belonging to the authenticated user."""
    tasks = await use_case.list_tasks(owner_id=user.id)
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        count=len(tasks),
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
async def get_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    use_case: TaskUseCase = Depends(get_task_use_case),
) -> TaskResponse:
    """Fetch a task by ID. Only the owner may access it."""
    try:
        task = await use_case.get_task(task_id=task_id, owner_id=user.id)
        return TaskResponse.model_validate(task)
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    user: User = Depends(get_current_user),
    use_case: TaskUseCase = Depends(get_task_use_case),
) -> TaskResponse:
    """Partially update a task. Only the owner may modify it."""
    try:
        task = await use_case.update_task(
            task_id=task_id,
            owner_id=user.id,
            title=body.title,
            description=body.description,
            status=body.status,
        )
        return TaskResponse.model_validate(task)
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    use_case: TaskUseCase = Depends(get_task_use_case),
) -> None:
    """Delete a task. Only the owner may delete it."""
    try:
        await use_case.delete_task(task_id=task_id, owner_id=user.id)
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
