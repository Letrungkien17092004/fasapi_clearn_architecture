"""Concrete auth service: JWK / JWKS validation with in-memory caching.

Implements the ``IAuthService`` port. Fetches public keys from a JWKS
endpoint, caches them in memory with a configurable TTL, and verifies
incoming JWTs using PyJWT.
"""

import asyncio
import time
from typing import Any

import jwt
import httpx

from app.domain.entities import User
from app.domain.exceptions import AuthenticationError


class JWKAuthService:
    """Async JWK auth service with an in-memory key cache.

    Parameters
    ----------
    jwks_url:
        URL of the JWKS endpoint (e.g. ``https://auth.example.com/.well-known/jwks.json``).
    audience:
        Expected ``aud`` claim in the JWT.
    issuer:
        Expected ``iss`` claim in the JWT.
    cache_ttl:
        Seconds to keep fetched keys in memory before re-fetching.
    """

    def __init__(
        self,
        jwks_url: str,
        audience: str = "",
        issuer: str = "",
        cache_ttl: int = 300,
    ) -> None:
        self._jwks_url = jwks_url
        self._audience = audience
        self._issuer = issuer
        self._cache_ttl = cache_ttl

        # Cache state — protected by an asyncio.Lock for thread safety.
        self._keys: dict[str, Any] = {}
        self._fetched_at: float = 0.0
        self._lock = asyncio.Lock()

    # ── Internal helpers ────────────────────────────────────────────

    async def _refresh_keys(self) -> None:
        """Fetch keys from the JWKS endpoint and update the cache.

        Only fetches if the cache has expired (TTL exceeded).
        """
        now = time.monotonic()
        if (now - self._fetched_at) < self._cache_ttl and self._keys:
            return

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self._jwks_url, timeout=10.0)
                resp.raise_for_status()
                jwks = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise AuthenticationError(
                    f"Failed to fetch JWKS keys: {exc}"
                ) from exc

        # Build a kid → public key mapping.
        new_keys: dict[str, Any] = {}
        for key_data in jwks.get("keys", []):
            kid = key_data.get("kid")
            if kid:
                new_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        self._keys = new_keys
        self._fetched_at = time.monotonic()

    async def _get_key(self, kid: str) -> Any:
        """Return the public key for *kid*, refreshing the cache if needed."""
        async with self._lock:
            await self._refresh_keys()

        key = self._keys.get(kid)
        if key is None:
            # One more refresh attempt in case the key was rotated.
            async with self._lock:
                self._fetched_at = 0.0  # force refresh
                await self._refresh_keys()
            key = self._keys.get(kid)

        if key is None:
            raise AuthenticationError(f"Unknown key id: {kid}")
        return key

    # ── IAuthService implementation ─────────────────────────────────

    async def verify_token(self, token: str) -> User:
        """Decode and validate a JWT, returning the authenticated User.

        Raises
        ------
        AuthenticationError
            If the token is malformed, expired, or signed by an unknown key.
        """
        # Extract the key id from the header (unverified).
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError as exc:
            raise AuthenticationError("Malformed JWT header") from exc

        kid = unverified_header.get("kid")
        if not kid:
            raise AuthenticationError("JWT header missing 'kid'")

        public_key = await self._get_key(kid)

        # Decode and verify the token.
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self._audience if self._audience else None,
                issuer=self._issuer if self._issuer else None,
                options={
                    "verify_aud": bool(self._audience),
                    "verify_iss": bool(self._issuer),
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthenticationError("Invalid audience") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthenticationError("Invalid issuer") from exc
        except jwt.DecodeError as exc:
            raise AuthenticationError(f"Token verification failed: {exc}") from exc

        # Map claims → User entity.
        return User(
            id=payload.get("sub", ""),
            email=payload.get("email", ""),
            name=payload.get("name", ""),
        )
