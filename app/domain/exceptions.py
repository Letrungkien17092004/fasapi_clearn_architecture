"""Core business exceptions — raised by domain logic and use cases."""


class DomainError(Exception):
    """Base class for all domain-layer errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class TaskNotFoundError(DomainError):
    """Raised when a task cannot be located by its identifier."""

    def __init__(self, task_id: str = "") -> None:
        message = f"Task not found: {task_id}" if task_id else "Task not found"
        super().__init__(message)


class TaskPermissionError(DomainError):
    """Raised when a user attempts an operation on a task they do not own."""

    def __init__(self, user_id: str = "", task_id: str = "") -> None:
        message = (
            f"User {user_id} is not authorized to access task {task_id}"
            if user_id and task_id
            else "Insufficient permissions for this task"
        )
        super().__init__(message)


class AuthenticationError(DomainError):
    """Raised when JWT validation or user identification fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)
