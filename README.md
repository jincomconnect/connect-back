# Connect Backend

Express + Mongo backend with JWT auth and a Python multi-agent orchestration sidecar.

## What We Built

The backend now supports a 5-stage multi-agent workflow:

1. research
2. architect
3. design
4. implement
5. test

Flow:

1. Client calls `POST /api/agents/run` on the Node backend.
2. Node validates JWT using existing auth middleware.
3. Node forwards the request to the Python orchestrator (`/orchestrate`).
4. Orchestrator runs all five stages and returns structured output.

Structured stage output fields:

- assumptions
- decisions
- artifacts
- open_questions
- confidence_score

## Architecture

- Node API: existing Express app (`app.js`, `server.js`).
- Agent proxy route: `routes/agents.js`.
- Orchestrator service: `ai-orchestrator/` (FastAPI + AutoGen-ready workflow).
- Stage contracts: `ai-orchestrator/app/schemas.py`.
- Stage prompt specs: `ai-orchestrator/app/agents.py`.
- Pipeline runner: `ai-orchestrator/app/workflow.py`.

## Prerequisites

- Node.js 18+ (required for global `fetch` in proxy route).
- Python 3.10+.

## Environment Setup

### Backend `.env`

Copy and edit:

```bash
cp .env.example .env
```

Important values:

- `PORT` (default `8080`)
- `MONGO_URI`
- `JWT_SECRET`
- `AUTOGEN_URL` (default `http://localhost:9000`)
- `ORCHESTRATOR_BEARER_TOKEN`
- `ORCHESTRATOR_TIMEOUT_MS` (default `60000`)

### Orchestrator `.env`

```bash
cd ai-orchestrator
cp .env.example .env
```

Important values:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `ORCHESTRATOR_BEARER_TOKEN` (must match backend)
- `PORT` (default `9000`)

## Run Locally

### 1) Install backend dependencies

```bash
npm install
```

### 2) Install orchestrator dependencies

```bash
npm run orchestrator:install
```

### 3) Start orchestrator

```bash
npm run orchestrator:dev
```

### 4) Start backend

In a second terminal:

```bash
npm run dev
```

## API Usage

### Auth

This route requires JWT auth. Use your existing login flow and send:

```http
Authorization: Bearer <jwt>
```

### Run multi-agent workflow

`POST /api/agents/run`

Request body:

```json
{
  "taskId": "feature-community-search-v1",
  "prompt": "Design and deliver community search with filters, pagination, and loading/empty/error states.",
  "productContext": "Frontend is React + Vite, backend is Express + Mongo, keep v1 incremental."
}
```

Successful response shape:

```json
{
  "task_id": "feature-community-search-v1",
  "created_at": "2026-05-06T00:00:00.000000+00:00",
  "stages": [
    {
      "stage": "research",
      "assumptions": [],
      "decisions": [],
      "artifacts": [{ "name": "...", "content": "..." }],
      "open_questions": [],
      "confidence_score": 0.8
    }
  ],
  "summary": "Workflow complete across 5 stages..."
}
```

## How To Update The Multi-Agent System

### Change stage behavior (prompts/objectives)

Edit:

- `ai-orchestrator/app/agents.py`

You can update each stage role/objective and prompt instructions.

### Change output schema

Edit:

- `ai-orchestrator/app/schemas.py`
- `ai-orchestrator/app/workflow.py` (parser/fallback handling)

If you add/remove fields, update both schema and parser.

### Change stage order

Edit:

- `ai-orchestrator/app/workflow.py` (`STAGES` list)

### Add approval gates

Recommended next step:

1. Stop after `design`.
2. Return a `pending_approval` status.
3. Add a second endpoint that resumes from `implement` after explicit approval.

### Add tool execution or code generation safety

Recommended:

- Keep implement stage read-only first (plans/patch proposals).
- Add hard limits (`max_turns`, timeout, budget).
- Add audit logs per task_id.

## Fallback Mode

If `OPENAI_API_KEY` is not set or model client import fails, orchestrator returns deterministic scaffold outputs so the workflow can still be tested end-to-end.

## Troubleshooting

- `Global fetch is unavailable`: run Node 18+.
- `401 Unauthorized` from orchestrator: ensure `ORCHESTRATOR_BEARER_TOKEN` matches in both services.
- `504 Orchestrator timeout`: increase `ORCHESTRATOR_TIMEOUT_MS` or reduce workload.
- No model responses: verify `OPENAI_API_KEY` in `ai-orchestrator/.env`.
