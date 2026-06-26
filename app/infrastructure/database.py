"""Async SQLAlchemy 2.0 engine and session factory.

This module owns the lifecycle of the async engine and session maker.
The `init_db` coroutine is called once at startup; `get_session` is an
async generator used by the Composition Root to inject sessions.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


# Module-level singletons — initialised by `init_db`.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str = "sqlite+aiosqlite:///./tasks.db") -> None:
    """Create the engine, session factory, and all tables.

    Call this once in the application lifespan (startup event).
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Import models so they register with Base.metadata before create_all.
    from app.infrastructure.models import TaskModel, UserModel  # noqa: F401

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a managed async session — use as a FastAPI dependency.

    The session is committed on success, rolled back on exception,
    and closed in the finally block.
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_db() -> None:
    """Dispose the engine — call at shutdown for graceful cleanup."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
