from __future__ import annotations

import os

import jwt as pyjwt
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .schemas import WorkflowRequest
from .workflow import run_workflow

load_dotenv()

app = FastAPI(title="Multi-Agent Orchestrator", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS — allow the same origins as the Node backend so the UI can reach us
# directly.  Set CLIENT_ORIGIN in .env to override (comma-separated).
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("CLIENT_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")


def _require_user(authorization: str | None) -> dict:
    """
    Validate a JWT Bearer token signed with the shared JWT_SECRET.
    Returns the decoded payload on success, raises HTTP 401/403 on failure.
    """
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        return pyjwt.decode(token, secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate")
async def orchestrate(
    request: WorkflowRequest,
    authorization: str | None = Header(default=None),
):
    _require_user(authorization)
    result = await run_workflow(request)
    return result.model_dump()
