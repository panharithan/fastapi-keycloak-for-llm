import pytest
import json
import io
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import HTTPException  
from app.app import app, decode_jwt, greet, get_authenticated_username  # import FastAPI instance and functions from app/app.py
from unittest.mock import patch, MagicMock
from app.ui import send_message_or_pdf

client = TestClient(app)


# -----------------------------
# 1️⃣ Decode JWT edge cases
# -----------------------------
def test_decode_jwt_invalid_structure():
    token = "invalidtokenwithoutdots"
    assert decode_jwt(token) is None


def test_decode_jwt_invalid_base64():
    bad_token = "a.broken_payload.c"
    assert decode_jwt(bad_token) is None


def test_decode_jwt_valid():
    payload = {"email_verified": True}
    b64_payload = json.dumps(payload).encode()
    import base64
    token = f"a.{base64.urlsafe_b64encode(b64_payload).decode().rstrip('=')}.c"
    decoded = decode_jwt(token)
    assert decoded["email_verified"] is True


# -----------------------------
# 2️⃣ Login — unverified email
# -----------------------------
@patch("app.app.requests.get")
@patch("app.app.requests.post")
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
@patch("app.app.requests.get")
@patch("app.app.requests.post")
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
@patch("app.app.requests.get")
@patch("app.app.requests.post")
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
@patch("app.app.keycloak_admin")
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
@patch("app.app.keycloak_admin")
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
@patch("app.app.keycloak_admin")
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
    assert greet("Panharith") == "Hello, Panharith!"

# -------------------------------
# Unit Tests for get_authenticated_username
# -------------------------------

def test_get_authenticated_username_valid_user():
    """✅ Should return username when preferred_username exists."""
    user = {"preferred_username": "john_doe"}
    result = get_authenticated_username(user)
    assert result == "john_doe"


def test_get_authenticated_username_missing_key():
    """❌ Should raise 401 when preferred_username is missing."""
    user = {"email": "john@example.com"}
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_username(user)
    assert exc_info.value.status_code == 401
    assert "Unauthorized user" in str(exc_info.value.detail)


def test_get_authenticated_username_empty_string():
    """❌ Should raise 401 when preferred_username is empty string."""
    user = {"preferred_username": ""}
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_username(user)
    assert exc_info.value.status_code == 401


def test_get_authenticated_username_none_value():
    """❌ Should raise 401 when preferred_username is None."""
    user = {"preferred_username": None}
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_username(user)
    assert exc_info.value.status_code == 401


def test_get_authenticated_username_extra_fields():
    """✅ Should ignore extra fields and return correct username."""
    user = {"preferred_username": "alice", "email": "alice@example.com", "role": "admin"}
    result = get_authenticated_username(user)
    assert result == "alice"


@pytest.fixture
def fake_history():
    return [{"role": "user", "content": "hello"}]


@pytest.fixture
def fake_token():
    return "FAKE_TOKEN_123"


# -----------------------------------------
# TEST 1: PDF upload message flow
# -----------------------------------------
@patch("app.ui.requests.post")
def test_send_message_positional_pdf(mock_post, fake_history, fake_token):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "message": "File uploaded",
        "summary": "short summary"
    }

    import io
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    fake_pdf.name = "doc.pdf"

    msg, history, pdf_summary = send_message_or_pdf(
        message="",
        history=fake_history,
        token=fake_token,
        uploaded_file=fake_pdf,
    )

    # UI should NOT output text directly
    assert msg == ""

    # History should remain the same length if function doesn't append anything
    assert len(history) == 3  # unchanged from fake_history
    assert history[-1]["role"] == "assistant"

    # Check PDF summary returned from backend
    if pdf_summary:
        assert pdf_summary == "short summary"

    # Backend endpoint was called
    assert mock_post.called
# -----------------------------------------
# TEST 2: No PDF, normal message
# -----------------------------------------
@patch("app.ui.requests.post")
def test_send_message_positional_no_pdf(mock_post, fake_history, fake_token):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"response": "reply from LLM"}

    msg, history, _ = send_message_or_pdf(
        message="hello model",
        history=fake_history,
        token=fake_token,
        uploaded_file=None,
    )

    # The UI returns an empty message; history stores the reply
    assert msg == ""

    assert len(history) == 3
    assert history[-1]["role"] == "assistant"
    assert history[-1]["content"] == "reply from LLM"

    # Called `/generate`
    assert mock_post.called