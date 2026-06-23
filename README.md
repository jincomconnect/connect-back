# Connect Backend

Backend repository for API services.

## Repository Layout

```text
connect-back/
  python-backend/       # main backend service for frontend API
```

## Service Port

- python-backend: 8000
- API base path: /api

## Run Locally

## Available Endpoints
- `GET /api/health`
- `POST /api/login`


### Demo Login
Request body:
```json
{
  "email": "demo@example.com",
  "password": "password123"
}
```

Successful responses return an `access_token`, `token_type`, and `user` object.
The demo credentials can be overridden with `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`, and `DEMO_USER_NAME` in `.env`.

```bash
cd python-backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Troubleshooting

- If startup fails, verify `.env` values and database connectivity.
- If dependencies fail, recreate `.venv` and reinstall with `pip install -e ".[dev]"`.
