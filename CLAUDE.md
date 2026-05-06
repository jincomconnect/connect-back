# Project: Social Media Backend (Python)

## Context
Asynchronous Python service for social networking (Users, Posts, Relationships). 
Built with FastAPI, Pydantic, and SQLAlchemy.

## Core Rules
- **Pythonic Code:** Follow PEP 8 standards strictly.
- **Type Safety:** Use Type Hints for all function signatures and variables.
- **Validation:** Use Pydantic models for all request/response schemas.
- **Security:** Use `passlib` for hashing and OAuth2 for auth. No raw SQL; use the ORM.

## Architectural Pattern: MVC
- **Models:** Managed in `app/models/` (SQLAlchemy/Django Models). Direct DB interactions only.
- **Controllers (Views):** Managed in `app/routers/` or `app/views/`. Handle request logic and orchestration.
- **Services (Business Logic):** Complex logic (e.g., feed generation) goes in `app/services/`.

## Tech Stack & Commands
- **Framework:** FastAPI / Django Rest Framework.
- **ORM:** SQLAlchemy / Django ORM.
- **Tests:** `pytest` (Aim for >90% coverage).
- **Linting:** `ruff check` and `ruff format`.

## Key Commands
- `uv run fastapi dev`: Start development server.
- `pytest`: Run all unit and integration tests.
- `alembic upgrade head`: Run database migrations.
- `ruff format .`: Format all files.

## File Structure
- `app/models/`: Database entities (User, Post, Follow).
- `app/schemas/`: Pydantic request/response models.
- `app/routers/`: API endpoints (Controllers).
- `app/services/`: Core social logic (e.g., `feed_service.py`).
- `app/middleware/`: Auth and logging handlers.

## Social Media Logic Constraints
- **Followers:** Prevent self-following. Use a many-to-many relationship table.
- **Feed:** Queries must be paginated by default.
- **Media:** Handle image uploads via `app/utils/storage.py`.