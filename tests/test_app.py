# Your main FastAPI entrypoint (as you already have).
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app, verification_tokens

client = TestClient(app)


# ---------------------------
# 1️⃣ Root Endpoint
# ---------------------------
def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Ollama LLM API" in resp.json()["message"]


# ---------------------------
# 2️⃣ Signup Validation Tests
# ---------------------------
@pytest.mark.parametrize("payload,expected_field", [
    ({"username": "a", "email": "test@example.com", "password": "Password1!", "first_name": "John", "last_name": "Doe"}, "username"),
    ({"username": "user123", "email": "bademail", "password": "Password1!", "first_name": "John", "last_name": "Doe"}, "email"),
    ({"username": "user123", "email": "test@example.com", "password": "weak", "first_name": "John", "last_name": "Doe"}, "password"),
    ({"username": "user123", "email": "test@example.com", "password": "Password1!", "first_name": "J", "last_name": "Doe"}, "first_name"),
])
def test_signup_validation_errors(payload, expected_field):
    resp = client.post("/signup", json=payload)
    assert resp.status_code == 422
    assert expected_field in resp.json()["message"]


# ---------------------------
# 3️⃣ Successful Signup Flow
# ---------------------------
@patch("app.keycloak_admin")
@patch("app.send_verification_email")
def test_signup_success(mock_send_email, mock_admin):
    mock_admin.realm_name = "llm"
    mock_admin.create_user.return_value = "/users/123"
    mock_admin.get_users.return_value = [{"id": "123"}]
    mock_admin.get_realm_roles.return_value = [{"name": "basic_user"}]
    mock_admin.assign_realm_roles.return_value = None

    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password1!",
        "first_name": "John",
        "last_name": "Doe"
    }

    resp = client.post("/signup", json=payload)
    assert resp.status_code == 200
    assert "Signup successful" in resp.json()["message"]

    mock_send_email.assert_called_once()
    assert len(verification_tokens) == 1


# ---------------------------
# 4️⃣ Email Verification Flow
# ---------------------------
@patch("app.keycloak_admin")
def test_email_verification_success(mock_admin):
    # Simulate token stored earlier
    verification_tokens["abc123"] = "user-id-1"
    mock_admin.update_user.return_value = None

    resp = client.get("/verify", params={"token": "abc123"})
    assert resp.status_code == 200
    assert "verified" in resp.json()["message"].lower()
    assert "abc123" not in verification_tokens  # token cleared


def test_email_verification_invalid():
    resp = client.get("/verify", params={"token": "invalid"})
    assert resp.status_code == 400
    assert "Invalid or expired token" in resp.json()["detail"]

# run test: pytest tests/test_app.py -v