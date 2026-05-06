# Python Backend Scaffold

This folder is a clean Python-first backend starting point.

It intentionally includes only:

- app wiring
- settings management
- logging setup
- health endpoint
- database placeholders

No business APIs are implemented yet.

## Quick Start

```bash
cd python-backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Structure

```text
python-backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    main.py
  tests/
  pyproject.toml
```

## Next Steps

1. Add auth domain models and schemas.
2. Add dependency injection for DB sessions/clients.
3. Add API routers by domain (`auth`, `users`, `communities`).
4. Add service and repository layers.
5. Add migrations strategy.
