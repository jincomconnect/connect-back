from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

from .schemas import WorkflowRequest
from .workflow import run_workflow

load_dotenv()

app = FastAPI(title="Multi-Agent Orchestrator", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate")
async def orchestrate(
    request: WorkflowRequest,
    authorization: str | None = Header(default=None),
):
    expected = os.getenv("ORCHESTRATOR_BEARER_TOKEN", "")
    if expected:
        if not authorization or authorization != f"Bearer {expected}":
            raise HTTPException(status_code=401, detail="Unauthorized")

    result = await run_workflow(request)
    return result.model_dump()
