import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
import app

client = TestClient(app.app)


# -----------------------------
# 1️⃣ Decode JWT edge cases
# -----------------------------
def test_decode_jwt_invalid_structure():
    token = "invalidtokenwithoutdots"
    assert app.decode_jwt(token) is None


def test_decode_jwt_invalid_base64(monkeypatch):
    bad_token = "a.broken_payload.c"
    assert app.decode_jwt(bad_token) is None


def test_decode_jwt_valid(monkeypatch):
    payload = {"email_verified": True}
    b64_payload = json.dumps(payload).encode()
    token = f"a.{app.base64.urlsafe_b64encode(b64_payload).decode().rstrip('=')}.c"
    decoded = app.decode_jwt(token)
    assert decoded["email_verified"] is True


# -----------------------------
# 2️⃣ Login — unverified email
# -----------------------------
@patch("app.requests.get")
@patch("app.requests.post")
def test_login_email_not_verified(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "access123",
        "refresh_token": "refresh123",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "sub": "user123",
        "email": "test@example.com",
        "email_verified": False
    }

    payload = {"username": "user123", "password": "Password1!"}
    resp = client.post("/login", json=payload)
    assert resp.status_code == 401
    assert "Email is not verified" in resp.text


# -----------------------------
# 3️⃣ Login — userinfo missing "email_verified"
# -----------------------------
@patch("app.requests.get")
@patch("app.requests.post")
def test_login_userinfo_missing_email_verified(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "access123",
        "refresh_token": "refresh123",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"sub": "user123", "email": "a@b.com"}
    resp = client.post("/login", json={"username": "user", "password": "Password1!"})
    assert resp.status_code == 200


# -----------------------------
# 4️⃣ Login — userinfo request fails → JWT fallback unverified
# -----------------------------
@patch("app.requests.get")
@patch("app.requests.post")
def test_login_userinfo_fallback_unverified(mock_post, mock_get):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "invalid.jwt.token",
        "refresh_token": "refresh123",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    mock_get.return_value.status_code = 500
    mock_get.return_value.text = "Internal Server Error"
    resp = client.post("/login", json={"username": "u", "password": "p"})
    assert resp.status_code == 401
    assert "Email is not verified" in resp.text


# -----------------------------
# 5️⃣ Signup — user not found after creation
# -----------------------------
@patch("app.keycloak_admin")
def test_signup_user_not_found_after_creation(mock_admin):
    mock_admin.realm_name = "llm"
    mock_admin.create_user.return_value = "/users/123"
    mock_admin.get_users.return_value = []
    payload = {
        "username": "userx",
        "email": "x@example.com",
        "password": "Password1!",
        "first_name": "John",
        "last_name": "Doe"
    }
    resp = client.post("/signup", json=payload)
    assert resp.status_code == 500
    assert "User not found" in resp.text


# -----------------------------
# 6️⃣ Signup — role missing
# -----------------------------
@patch("app.keycloak_admin")
def test_signup_role_not_found(mock_admin):
    mock_admin.create_user.return_value = "/users/123"
    mock_admin.get_users.return_value = [{"id": "123"}]
    mock_admin.get_realm_roles.return_value = []
    payload = {
        "username": "userx",
        "email": "x@example.com",
        "password": "Password1!",
        "first_name": "John",
        "last_name": "Doe"
    }
    resp = client.post("/signup", json=payload)
    assert resp.status_code == 500
    assert "Role 'basic_user' not found" in resp.text


# -----------------------------
# 7️⃣ Resend verification — email already verified
# -----------------------------
@patch("app.keycloak_admin")
def test_resend_verification_already_verified(mock_admin):
    mock_admin.get_users.return_value = [{
        "username": "userx",
        "email": "x@example.com",
        "emailVerified": True
    }]
    resp = client.post("/resend-verification", json={"username": "userx"})
    assert resp.status_code == 200
    assert "already verified" in resp.text


# -----------------------------
# 8️⃣ Verify — invalid token
# -----------------------------
def test_verify_invalid_token():
    resp = client.get("/verify", params={"token": "doesnotexist"})
    assert resp.status_code == 400
    assert "Invalid or expired token" in resp.text


# -----------------------------
# 9️⃣ Validation error handler (friendly)
# -----------------------------
def test_validation_handler_custom_format():
    resp = client.post("/signup", json={})
    assert resp.status_code == 422
    json_body = resp.json()
    assert json_body["status"] == "error"
    assert "message" in json_body


# -----------------------------
# 🔟 Gradio greet coverage
# -----------------------------
def test_greet_function():
    assert app.greet("Panharith") == "Hello, Panharith!"
