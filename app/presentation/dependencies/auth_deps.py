"""Composition Root — authentication dependency.

Implements the ``HTTPBearer`` security scheme that extracts the JWT
from the ``Authorization`` header and validates it via ``IAuthService``.

    Router
      └─ Depends(get_current_user)
           └─ HTTPBearer → IAuthService.verify_token(token)

The concrete ``JWKAuthService`` is instantiated once at startup and
stored in ``app.state.auth_service`` by ``main.py``.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.interfaces.auth_service import IAuthService
from app.domain.entities import User
from app.domain.exceptions import AuthenticationError

# Reusable security scheme — produces the raw token string.
_bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> User:
    """Extract and verify the JWT, returning the authenticated User.

    This dependency is placed on any protected route:

        @router.get("/tasks", dependencies=[Depends(get_current_user)])

    or used directly when the User entity is needed:

        user: User = Depends(get_current_user)
    """
    # Retrieve the auth service that was wired at startup.
    auth_service: IAuthService | None = getattr(request.app.state, "auth_service", None)
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service not configured",
        )

    try:
        return await auth_service.verify_token(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc.message),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
