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

## Run Dev Server

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

# Start in development mode
npm run dev:backend

# Or manually with specific environment:
APP_ENV=development uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
APP_ENV=test uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Troubleshooting

## Environment-Specific Demo Accounts

Each environment has its own demo credentials and database:

| Environment | Email | Password | Port | Database |
|---|---|---|---|---|
| **development** | `dev@example.com` | `dev-password123` | 8000 | `connect-dev` |
| **test** | `test@example.com` | `test-password123` | 8001 | `connect-test` |
| **production** | `admin@example.com` | `change-me-in-production` | 8000 | `connect-prod` |

Set `APP_ENV` to switch environments. The backend will automatically load the corresponding `.env.*` file.

- If startup fails, verify `.env` values and database connectivity.
- If dependencies fail, recreate `.venv` and reinstall with `pip install -e ".[dev]"`.
