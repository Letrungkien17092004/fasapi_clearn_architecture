"""Domain Entity: User — pure Python, no framework dependencies."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    """Core user entity representing an authenticated principal."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""
