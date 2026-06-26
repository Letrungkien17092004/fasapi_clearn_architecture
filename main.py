"""Application entry point — assembles all layers.

This is the Composition Root at the top level. It:
1. Creates the FastAPI app.
2. Initialises the database (Infrastructure).
3. Instantiates JWKAuthService and stores it on ``app.state``.
4. Includes the Presentation routers.

Run with:
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.infrastructure.auth.jwk_service import JWKAuthService
from app.infrastructure.database import dispose_db, init_db
from app.presentation.routers.task_router import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hooks.

    Startup:
        - Initialise the async database engine and create tables.
        - Create the JWK auth service and attach it to app.state.

    Shutdown:
        - Dispose the database engine gracefully.
    """
    # ── Startup ─────────────────────────────────────────────────────
    await init_db("sqlite+aiosqlite:///./tasks.db")

    # In production, point to a real JWKS endpoint.
    # For local dev / testing, this is a placeholder.
    auth_service = JWKAuthService(
        jwks_url="https://your-idp.example.com/.well-known/jwks.json",
        audience="task-management-api",
        issuer="https://your-idp.example.com",
        cache_ttl=300,
    )
    app.state.auth_service = auth_service

    yield  # ← app is running

    # ── Shutdown ────────────────────────────────────────────────────
    await dispose_db()


def create_app() -> FastAPI:
    """Application factory — returns a fully-configured FastAPI instance."""
    app = FastAPI(
        title="Enterprise Task Management API",
        description="Clean Architecture with FastAPI — Composition Root pattern",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routers.
    app.include_router(task_router, prefix="/api/v1")

    # Health check (unprotected).
    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


# Module-level app instance for `uvicorn main:app`.
app = create_app()
