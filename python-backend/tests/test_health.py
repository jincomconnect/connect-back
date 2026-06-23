from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "demo@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "demo-token-demo@example.com",
        "token_type": "bearer",
        "user": {"email": "demo@example.com", "name": "Demo User"},
    }


def test_login_endpoint_rejects_invalid_credentials() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/login",
        json={"email": "demo@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
