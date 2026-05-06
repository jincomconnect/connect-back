# Connect Backend

This repository contains your backend code and the AI orchestrator sidecar.

## Repository Layout

```text
connect-back/
  python-backend/       # your main backend service for frontend API
  ai-orchestrator/      # 4-agent Claude pipeline service
```

## Current Deployment Model

- Keep both services in this same repository.
- Run them on different ports.
- For now, orchestrator runs in local open mode (no JWT required).

## Service Ports

- python-backend: 8000
- ai-orchestrator: 9000

## Run Locally

Open two terminals.

### Terminal 1: python-backend

```bash
cd python-backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2: ai-orchestrator

```bash
cd ai-orchestrator
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 9000
```

## Orchestrator Environment

Set these in ai-orchestrator/.env:

```env
CLIENT_ORIGIN=http://localhost:5173,http://127.0.0.1:5173
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_OPUS_MODEL=claude-opus-4-5
CLAUDE_SONNET_MODEL=claude-sonnet-4-5
CLAUDE_HAIKU_MODEL=claude-haiku-3-5
PORT=9000
```

## Orchestrator API

### Health

```http
GET /health
```

### Run 4-agent pipeline

```http
POST /orchestrate
Content-Type: application/json
```

Request body:

```json
{
  "prompt": "Add a community search endpoint with keyword filtering and pagination.",
  "product_context": "Use existing backend patterns from python-backend/app and keep API backward compatible."
}
```

task_id is optional. If omitted, a UUID is generated automatically.

## Lightweight Runner UI

You can run the pipeline from a browser without curl.

1. Start both services:
  - python-backend on port 8000
  - ai-orchestrator on port 9000
2. Open:
  - http://localhost:9000/runner
3. In the page:
  - Set Orchestrator Base URL (default http://localhost:9000)
  - Choose target repository (backend or frontend)
  - Enter prompt and optional product context
  - Click Run Agents

The UI calls /orchestrate directly and prints full JSON output, including architect, worker, tester, and reviewer stages.

## Optional Future Split: Move ai-orchestrator to Separate Repository

If you later want a dedicated repo for the orchestrator, this is a good and clean split. Keep python-backend here and extract only ai-orchestrator.

### Option A: subtree split (recommended)

```bash
cd connect-back
git subtree split --prefix=ai-orchestrator -b ai-orchestrator-history
git init ../ai-orchestrator-repo
cd ../ai-orchestrator-repo
git pull ../connect-back ai-orchestrator-history
```

This preserves ai-orchestrator commit history.

### Option B: copy-only bootstrap

Copy ai-orchestrator folder into a new repository and initialize git there. Faster, but history is not preserved.

## Troubleshooting

- 401/403 on /orchestrate: if you still see this, restart orchestrator to load the latest auth-disabled code.
- ModuleNotFoundError for autogen_ext.models.anthropic: reinstall ai-orchestrator dependencies.
- Pipeline returns fallback mode BLOCKED: set ANTHROPIC_API_KEY and restart service.
