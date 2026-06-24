from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from app.core.settings import get_settings
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, LoginResponse, LoginUser, SignupRequest

api_router = APIRouter(prefix="/api")

``
_fallback_users: dict[str, dict[str, str]] = {}


def _get_auth_repository() -> AuthRepository | None:
    try:
        return AuthRepository()
    except PyMongoError:
        # Allow local API/testing to run even when MongoDB is unavailable.
        return None


def _build_auth_response(email: str, name: str) -> LoginResponse:
    return LoginResponse(
        access_token=f"demo-token-{email}",
        user=LoginUser(email=email, name=name),
    )


@api_router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.post("/login", response_model=LoginResponse, tags=["auth"])
def login(payload: LoginRequest) -> LoginResponse:
    settings = get_settings()
    email = str(payload.email)

    repository = _get_auth_repository()
    if repository is not None:
        try:
            stored_user = repository.get_by_email(email)

            if stored_user and payload.password == stored_user["password"]:
                return _build_auth_response(email, stored_user["name"])
        except PyMongoError:
            pass

    fallback_user = _fallback_users.get(email)

    if fallback_user and payload.password == fallback_user["password"]:
        return _build_auth_response(email, fallback_user["name"])

    if email != settings.demo_user_email or payload.password != settings.demo_user_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return _build_auth_response(email, settings.demo_user_name)


@api_router.post(
    "/signup",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
def signup(payload: SignupRequest) -> LoginResponse:
    settings = get_settings()
    email = str(payload.email)

    if email == settings.demo_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    repository = _get_auth_repository()

    if repository is not None:
        try:
            existing_user = repository.get_by_email(email)
            if existing_user is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )

            created = repository.create_user(email=email, name=payload.name, password=payload.password)
            if not created:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )
        except PyMongoError:
            if email in _fallback_users:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )

            _fallback_users[email] = {
                "name": payload.name,
                "password": payload.password,
            }
    else:
        if email in _fallback_users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        _fallback_users[email] = {
            "name": payload.name,
            "password": payload.password,
        }

    return _build_auth_response(email, payload.name)
