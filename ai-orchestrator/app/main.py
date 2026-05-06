from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, Field

from .schemas import WorkflowRequest
from .workflow import run_workflow


class KeyValidationRequest(BaseModel):
    api_key: str = Field(min_length=1)

load_dotenv()

app = FastAPI(title="Multi-Agent Orchestrator", version="0.1.0")
_RUNNER_HTML = Path(__file__).parent / "static" / "runner.html"

_raw_origins = os.getenv("CLIENT_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/validate-key")
async def validate_key(body: KeyValidationRequest) -> dict:
    """
    Make a minimal Anthropic API call (list models) to confirm the key is valid.
    Never logs or stores the key.
    """
    import httpx

    key = body.api_key.strip()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                },
            )
        if r.status_code == 200:
            return {"valid": True, "message": "API key is valid."}
        elif r.status_code == 401:
            return {"valid": False, "message": "Invalid API key (401 Unauthorized)."}
        else:
            return {"valid": False, "message": f"Anthropic returned HTTP {r.status_code}."}
    except Exception as exc:
        return {"valid": False, "message": f"Request failed: {exc}"}


@app.get("/runner", response_class=HTMLResponse)
def runner() -> str:
    if not _RUNNER_HTML.exists():
        raise HTTPException(status_code=404, detail="Runner UI not found")
    return _RUNNER_HTML.read_text(encoding="utf-8")


@app.post("/orchestrate")
async def orchestrate(request: WorkflowRequest):
    result = await run_workflow(request)
    return result.model_dump()
