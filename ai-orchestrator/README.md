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

## Backend Integration (Python API)

Python backend endpoint:

- `POST /api/agents/run`

Request body:

```json
{
  "taskId": "feature-community-search-v1",
  "prompt": "Build ...",
  "productContext": "optional context"
}
```

Required Python backend env vars:

- `AUTOGEN_URL=http://localhost:9000`
- `ORCHESTRATOR_BEARER_TOKEN=change-me`

## Prompt Execution Flow

For each request, the orchestrator runs stages in this fixed order:

1. `research`
2. `architect`
3. `design`
4. `implement`
5. `test`

Each stage receives the same base inputs (`task_id`, `prompt`, `product_context`) plus prior stage outputs as context. This creates a chained execution where later stages build on earlier decisions.

```text
prompt + product_context
  -> research output
  -> architect output (research-aware)
  -> design output (research + architect-aware)
  -> implement output (all prior context)
  -> test output (all prior context)
```

## Example Request + Stage Behavior

Example request:

```json
{
  "task_id": "feature-community-search-v1",
  "prompt": "Design and deliver community search with filters, pagination, and loading/empty/error states.",
  "product_context": "Frontend is React + Vite, backend is FastAPI + Mongo, keep v1 incremental."
}
```

How the stages typically interpret it:

- `research`: identifies constraints, unknowns, and initial risks.
- `architect`: proposes high-level service/data strategy and trade-offs.
- `design`: defines API/data contracts and user-state behavior.
- `implement`: outputs concrete implementation steps and deliverables.
- `test`: outputs validation strategy and specific test cases.

All stages return the same schema keys:

- `assumptions`
- `decisions`
- `artifacts`
- `open_questions`
- `confidence_score`

## Notes

- If `OPENAI_API_KEY` is missing, the service runs in deterministic fallback mode for pipeline testing.
- Fallback mode is useful for schema/workflow integration before enabling model calls.
