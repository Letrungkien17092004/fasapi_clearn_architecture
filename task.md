# Implementation Plan - Enterprise Core

Execute step-by-step. Stop after completing each task and wait for my instruction.

## Task 1: Domain & Application Interfaces
- Define Domain Entities (`User`, `Task`).
- Define Application Ports (`ITaskRepository`, `IAuthService`) using `abc.ABC`.
- Define core business exceptions.

## Task 2: Advanced Infrastructure (DB & JWK)
- Implement Async SQLAlchemy 2.0 setup with `async_sessionmaker`.
- Implement `SQLAlchemyTaskRepository` inheriting from `ITaskRepository`. Ensure mapping from ORM models to Domain Entities.
- Implement `JWKAuthService` inheriting from `IAuthService` with an in-memory async cache mechanism for public keys.

## Task 3: Presentation & Composition Root (The DI Wiring)
- Create factory functions in `presentation/dependencies/` to assemble dependencies (`get_db_session` -> `get_task_repo` -> `get_use_case`).
- Implement the FastAPI `HTTPBearer` security scheme that leverages the wired `IAuthService`.
- Create routers for `/tasks` protecting them with the JWK auth dependency.

## Task 4: Integration & Verification
- Create `main.py` combining all modules.
- Provide a robust mock test using `pytest-asyncio` demonstrating how to test the Use Case by mocking the repository interface without spinning up a real database or framework.