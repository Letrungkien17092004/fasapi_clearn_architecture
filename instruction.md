# Enterprise Architectural Guidelines (FastAPI Clean Architecture)

## 1. Advanced Tech Stack
- Framework: FastAPI (Async)
- ORM: SQLAlchemy 2.0 (Async Session)
- Auth: JWK (JSON Web Key) Validation for JWT using PyJWT/Authlib
- Dependency Injection Pattern: Composition Root using FastAPI Depends factories

## 2. Strict Layer Isolation Rules
1. Domain Layer: Pure Python. No pydantic, no sqlalchemy, no fastapi. Contains pure entities and domain exceptions.
2. Application Layer: Contains Use Cases and Interfaces (Abstract classes). No infrastructure references.
3. Infrastructure Layer: Implements Application interfaces. Handles database sessions, external API calls, JWK key fetching & caching.
4. Presentation Layer: Composition Root. This layer is allowed to know about both Application and Infrastructure to perform Dependency Injection wiring using FastAPI `Depends`.

## 3. DB Dependency Inversion Pattern
To prevent infrastructure leakage into the core, use factory dependencies in the presentation layer:
`FastAPI Router -> Depends(GetUseCase) -> Inject Concrete Repo -> Inject AsyncSession`
The Use Case itself must only accept the abstract repository interface in its constructor.

## 4. JWK Authentication Design
- Define `IAuthService` in Application layer.
- Implement `JWKAuthService` in Infrastructure layer (handles fetching public keys from JWKS endpoints and caching them).
- Create an `HTTPBearer` security dependency in Presentation layer that utilizes `IAuthService`.