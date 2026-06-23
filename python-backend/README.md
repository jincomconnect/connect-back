# Python Backend Scaffold

This folder is a clean Python-first backend starting point.

It intentionally includes only:

- app wiring
- settings management
- logging setup
- `/api/health` endpoint
- `/api/login` endpoint
- database placeholders

Business APIs now include a health check and a demo login endpoint.

## Quick Start

## API Endpoints
- `GET /api/health`
- `POST /api/login`

### Demo Login Request
```json
{
  "email": "demo@example.com",
  "password": "password123"
}
```

### Demo Login Response
```json
{
  "access_token": "demo-token-demo@example.com",
  "token_type": "bearer",
  "user": {
    "email": "demo@example.com",
    "name": "Demo User"
  }
}
```

Override the defaults with `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`, and `DEMO_USER_NAME` in `.env`.

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

1. Replace the demo login check with a real user model and password hashing.
2. Add dependency injection for DB sessions and clients.
3. Split auth logic into dedicated service and repository layers.
4. Add token signing plus authenticated routes such as `/api/me`.
5. Add a migrations strategy.
