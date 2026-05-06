# Connect Backend

Backend repository for API services.

## Repository Layout

```text
connect-back/
  python-backend/       # main backend service for frontend API
```

## Service Port

- python-backend: 8000

## Run Locally

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
