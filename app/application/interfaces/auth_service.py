"""Application Port: Auth Service — abstract contract for JWT / JWK validation."""

from abc import ABC, abstractmethod

from app.domain.entities import User


class IAuthService(ABC):
    """Interface that any authentication adapter must implement.

    The Application layer uses this to verify tokens and retrieve the
    authenticated user without knowing how keys are fetched or cached.
    """

    @abstractmethod
    async def verify_token(self, token: str) -> User:
        """Validate a JWT and return the authenticated User entity.

        Raises:
            AuthenticationError: If the token is expired, malformed,
                or signed by an unknown key.
        """
