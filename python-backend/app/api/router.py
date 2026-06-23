from fastapi import APIRouter, HTTPException, status

from app.core.settings import get_settings
from app.schemas.auth import LoginRequest, LoginResponse, LoginUser

api_router = APIRouter(prefix="/api")


@api_router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.post("/login", response_model=LoginResponse, tags=["auth"])
def login(payload: LoginRequest) -> LoginResponse:
    settings = get_settings()

    if payload.email != settings.demo_user_email or payload.password != settings.demo_user_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return LoginResponse(
        access_token=f"demo-token-{payload.email}",
        user=LoginUser(email=payload.email, name=settings.demo_user_name),
    )
