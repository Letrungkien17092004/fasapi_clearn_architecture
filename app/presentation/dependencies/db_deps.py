"""Composition Root — database session dependency.

Provides the async session as a FastAPI dependency. The session is
managed by the infrastructure layer (commit/rollback/close).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session for the duration of a request.

    This is the bottom of the dependency chain — every other factory
    that needs a session depends on this.
    """
    async for session in get_session():
        yield session
