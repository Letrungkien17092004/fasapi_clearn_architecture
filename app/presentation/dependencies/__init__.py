"""Composition Root — dependency injection wiring.

This module is the ONLY place that knows about both Application
interfaces and Infrastructure implementations. It assembles the
dependency graph using FastAPI ``Depends`` factories:

    Router → Depends(get_use_case) → injects Repo → injects Session
"""

from app.presentation.dependencies.task_deps import get_task_use_case
from app.presentation.dependencies.auth_deps import get_current_user
from app.presentation.dependencies.db_deps import get_db_session

__all__ = ["get_current_user", "get_db_session", "get_task_use_case"]
