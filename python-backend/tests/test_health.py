from fastapi.testclient import TestClient

from app.main import app
from app.api import router
from app.db.session import close_mongo_client


def setup_function() -> None:
    router._fallback_users.clear()
    close_mongo_client()


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "dev@example.com", "password": "dev-password123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "demo-token-dev@example.com",
        "token_type": "bearer",
        "user": {"email": "dev@example.com", "name": "Development User"},
    }


def test_login_endpoint_rejects_invalid_credentials() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "dev@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_signup_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/signup",
        json={
            "name": "New User",
            "email": "new.user@example.com",
            "password": "new-password123",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "access_token": "demo-token-new.user@example.com",
        "token_type": "bearer",
        "user": {"email": "new.user@example.com", "name": "New User"},
    }


def test_signup_then_login_with_new_account() -> None:
    client = TestClient(app)
    signup_response = client.post(
        "/api/signup",
        json={
            "name": "Signup Login User",
            "email": "signup.login@example.com",
            "password": "signup-password123",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/login",
        json={"email": "signup.login@example.com", "password": "signup-password123"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"] == {
        "email": "signup.login@example.com",
        "name": "Signup Login User",
    }


def test_signup_rejects_duplicate_email() -> None:
    client = TestClient(app)
    first_response = client.post(
        "/api/signup",
        json={
            "name": "Duplicate User",
            "email": "duplicate.user@example.com",
            "password": "duplicate-password123",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/signup",
        json={
            "name": "Duplicate User Again",
            "email": "duplicate.user@example.com",
            "password": "duplicate-password123",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "An account with this email already exists"}
