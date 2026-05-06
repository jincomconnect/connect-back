# Multi-Agent Orchestrator (AutoGen-ready)

This service provides a 5-stage multi-agent pipeline:

1. research
2. architect
3. design
4. implement
5. test

Each stage returns strict structured output with:

- assumptions
- decisions
- artifacts
- open_questions
- confidence_score

## Quick Start

### 1) Create and activate virtual environment

```bash
cd connect-back/ai-orchestrator
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
```

Set values in `.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `ORCHESTRATOR_BEARER_TOKEN`
- `PORT`

### 4) Run service

```bash
uvicorn app.main:app --reload --port 9000
```

### 5) Test endpoint directly

```bash
curl -X POST http://localhost:9000/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change-me" \
  --data @examples/feature-request.json
```

## Backend Integration (Node API)

Node endpoint:

- `POST /api/agents/run`

Request body:

```json
{
  "taskId": "feature-community-search-v1",
  "prompt": "Build ...",
  "productContext": "optional context"
}
```

Required backend env vars:

- `AUTOGEN_URL=http://localhost:9000`
- `ORCHESTRATOR_BEARER_TOKEN=change-me`
- `ORCHESTRATOR_TIMEOUT_MS=60000`

## Notes

- If `OPENAI_API_KEY` is missing, the service runs in deterministic fallback mode for pipeline testing.
- Fallback mode is useful for schema/workflow integration before enabling model calls.
