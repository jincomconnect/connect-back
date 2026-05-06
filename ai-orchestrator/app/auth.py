from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from .db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    message: str
    token: str
    user: dict


class UserResponse(BaseModel):
    user: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")
    return secret


def _make_token(user_id: str, email: str) -> str:
    payload = {
        "userId": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return pyjwt.encode(payload, _jwt_secret(), algorithm="HS256")


def _auth_response(user: dict, message: str) -> AuthResponse:
    uid = str(user["_id"])
    return AuthResponse(
        message=message,
        token=_make_token(uid, user["email"]),
        user={"id": uid, "email": user["email"]},
    )


async def _require_user(authorization: str | None = Header(default=None)) -> dict:
    """Dependency — validates JWT and returns the decoded payload."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        return pyjwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(body: SignupRequest):
    db = get_db()
    email = body.email.lower().strip()

    if await db["users"].find_one({"email": email}):
        raise HTTPException(status_code=400, detail="User already exists")

    result = await db["users"].insert_one({
        "email": email,
        "password": _pwd.hash(body.password),
        "createdAt": datetime.now(timezone.utc),
    })

    user = await db["users"].find_one({"_id": result.inserted_id})
    return _auth_response(user, "User created successfully")


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    db = get_db()
    email = body.email.lower().strip()

    user = await db["users"].find_one({"email": email})
    if not user or not _pwd.verify(body.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return _auth_response(user, "Login successful")


@router.get("/me", response_model=UserResponse)
async def me(payload: dict = Depends(_require_user)):
    db = get_db()
    user = await db["users"].find_one(
        {"_id": ObjectId(payload["userId"])},
        {"_id": 1, "email": 1},
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(user={"id": str(user["_id"]), "email": user["email"]})


@router.get("/protected")
async def protected(payload: dict = Depends(_require_user)):
    return {
        "message": "This is a protected route",
        "userId": payload["userId"],
        "email": payload["email"],
    }
