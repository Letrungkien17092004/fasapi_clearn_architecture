"""Composition Root — task use-case dependency chain.

    Router
      └─ Depends(get_task_use_case)
           └─ SQLAlchemyTaskRepository(session)
                └─ Depends(get_db_session)

The use case only sees ``ITaskRepository`` — it never knows that
``SQLAlchemyTaskRepository`` or ``AsyncSession`` exist.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.task_use_case import TaskUseCase
from app.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository
from app.presentation.dependencies.db_deps import get_db_session


async def get_task_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> TaskUseCase:
    """Assemble and return a fully-wired TaskUseCase.

    1. Receive a managed async session from the DB dependency.
    2. Create a concrete repository bound to that session.
    3. Inject the repository into the use case.
    4. Return the use case to the router.
    """
    repository = SQLAlchemyTaskRepository(session)
    return TaskUseCase(repository)
