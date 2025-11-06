import pytest
import base64
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

# Import everything from app.app (your actual FastAPI app module)
from app.app import (
    app,
    keycloak_admin,
    verification_tokens,
    get_current_user,
    decode_jwt,
    validation_exception_handler,
    SignupData,
    send_verification_email,
    verify_token,
)

client = TestClient(app)


# ------------------------------------------------------------------------------------
# 1. Secure endpoint unauthenticated - invalid token (covers token verification failure)
# ------------------------------------------------------------------------------------
@patch("app.app.verify_token", side_effect=Exception("Invalid token"))
def test_secure_endpoint_unauthenticated(mock_verify):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/secure-endpoint", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] in ["Invalid token", "Error decoding token headers."]


# ------------------------------------------------------------------------------------
# 2. Signup: Keycloak create_user fails (simulate API failure)
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.create_user", side_effect=Exception("Keycloak API error"))
def test_signup_keycloak_create_user_failure(mock_create_user):
    payload = {
        "username": "valid_user",
        "email": "test@example.com",
        "password": "Valid123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code in (400, 422, 500)


# ------------------------------------------------------------------------------------
# 3. Signup: user not found after creation
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.create_user", return_value="/users/123")
@patch("app.app.keycloak_admin.get_users", return_value=[])
def test_signup_user_not_found_after_creation(mock_get_users, mock_create_user):
    payload = {
        "username": "valid_user",
        "email": "test@example.com",
        "password": "Valid123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "User not found after creation"


# ------------------------------------------------------------------------------------
# 4. Signup: role not found
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.create_user", return_value="/users/123")
@patch("app.app.keycloak_admin.get_users", return_value=[{"id": "123"}])
@patch("app.app.keycloak_admin.get_realm_roles", return_value=[])
def test_signup_role_not_found(mock_roles, mock_get_users, mock_create_user):
    payload = {
        "username": "valid_user",
        "email": "test@example.com",
        "password": "Valid123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 500
    assert response.json()["detail"] == "Role 'basic_user' not found"


# ------------------------------------------------------------------------------------
# 5. Verify endpoint invalid token
# ------------------------------------------------------------------------------------
def test_verify_invalid_token():
    response = client.get("/verify?token=nonexistenttoken")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


# ------------------------------------------------------------------------------------
# 6. Resend verification: user not found
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.get_users", return_value=[])
def test_resend_verification_user_not_found(mock_get_users):
    response = client.post("/resend-verification", json={"username": "nonexistent"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


# ------------------------------------------------------------------------------------
# 7. Resend verification: email missing
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.get_users", return_value=[{"id": "123", "username": "user1"}])
def test_resend_verification_no_email(mock_get_users):
    response = client.post("/resend-verification", json={"username": "user1"})
    assert response.status_code == 400
    assert "does not have an email configured" in response.json()["detail"]


# ------------------------------------------------------------------------------------
# 8. Resend verification: email already verified
# ------------------------------------------------------------------------------------
@patch("app.app.keycloak_admin.get_users", return_value=[{
    "id": "123", "username": "user1", "email": "user1@example.com", "emailVerified": True
}])
def test_resend_verification_email_already_verified(mock_get_users):
    response = client.post("/resend-verification", json={"username": "user1"})
    assert response.status_code == 200
    assert "already verified" in response.json()["message"]


# ------------------------------------------------------------------------------------
# 9. Validation error handler (422)
# ------------------------------------------------------------------------------------
def test_validation_exception_handler():
    payload = {
        "username": "us",
        "email": "notanemail",
        "password": "short",
        "first_name": "J",
        "last_name": "D"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 422
    json_resp = response.json()
    assert json_resp["status"] == "error"
    assert "username" in json_resp["message"]
    assert "email" in json_resp["message"]
    assert "password" in json_resp["message"]
    assert "first_name" in json_resp["message"]
    assert "last_name" in json_resp["message"]


# ------------------------------------------------------------------------------------
# 10. Gradio UI smoke test
# ------------------------------------------------------------------------------------
def test_gradio_ui_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ollama LLM API" in response.json()["message"]


# ------------------------------------------------------------------------------------
# 11. SignupData validators (covers 41–47)
# ------------------------------------------------------------------------------------
def test_invalid_username_pattern():
    with pytest.raises(ValidationError):
        SignupData(username="@@@", email="a@b.com", password="Password1!", first_name="John", last_name="Doe")

def test_invalid_password_missing_uppercase():
    with pytest.raises(ValidationError):
        SignupData(username="john", email="a@b.com", password="password1!", first_name="John", last_name="Doe")

def test_invalid_first_name_pattern():
    with pytest.raises(ValidationError):
        SignupData(username="john", email="a@b.com", password="Password1!", first_name="J1", last_name="Doe")

def test_invalid_last_name_pattern():
    with pytest.raises(ValidationError):
        SignupData(username="john", email="a@b.com", password="Password1!", first_name="John", last_name="D1")


# ------------------------------------------------------------------------------------
# 12. get_current_user invalid token (covers 73, 80)
# ------------------------------------------------------------------------------------
def test_get_current_user_invalid_token():
    with patch("app.app.verify_token", side_effect=Exception("Invalid token")):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="badtoken")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------------------------
# 13. decode_jwt invalid base64 (covers 139)
# ------------------------------------------------------------------------------------
def test_decode_jwt_invalid_structure():
    invalid_token = "header.invalid_payload.signature"
    result = decode_jwt(invalid_token)
    assert result is None


# ------------------------------------------------------------------------------------
# 14. resend-verification success (covers 218–225)
# ------------------------------------------------------------------------------------
def test_resend_verification_success():
    mock_user = {"id": "1", "username": "user", "email": "test@example.com", "emailVerified": False}
    with patch("app.app.keycloak_admin.get_users", return_value=[mock_user]):
        with patch("app.app.send_verification_email") as mock_send_email:
            response = client.post("/resend-verification", json={"username": "user"})
            assert response.status_code == 200
            assert "Verification email resent" in response.json()["message"]
            mock_send_email.assert_called_once()


# ------------------------------------------------------------------------------------
# 15. validation_exception_handler direct test (covers 232–234)
# ------------------------------------------------------------------------------------
def test_validation_exception_handler_direct():
    exc = RequestValidationError([{"loc": ("body", "username"), "msg": "Invalid username"}])
    request = Request(scope={"type": "http"})
    response: JSONResponse = asyncio.run(validation_exception_handler(request, exc))
    assert response.status_code == 422
    assert "Invalid username" in response.body.decode()


# ------------------------------------------------------------------------------------
# Additional tests for SignupData validators and decode_jwt success
# ------------------------------------------------------------------------------------

def test_signupdata_valid_data():
    data = SignupData(
        username="valid_user",
        email="test@example.com",
        password="Valid123!",
        first_name="John",
        last_name="Doe"
    )
    assert data.username == "valid_user"
    assert data.email == "test@example.com"


def test_get_current_user_success():
    valid_payload = {"preferred_username": "john"}
    with patch("app.app.verify_token", return_value=valid_payload):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="validtoken")
        user = get_current_user(creds)
        assert user["preferred_username"] == "john"


def test_decode_jwt_success():
    payload = {"sub": "123"}
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    token = f"header.{b64_payload}.signature"
    result = decode_jwt(token)
    assert result == payload


def test_signupdata_valid_first_and_last_name():
    data = SignupData(username="user123", email="a@b.com", password="Valid123!", first_name="Jane", last_name="Doe")
    assert data.first_name == "Jane"
    assert data.last_name == "Doe"


def test_get_current_user_exception_path():
    with patch("app.app.verify_token", side_effect=ValueError("Token error")):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token123")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(creds)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid token"


def test_decode_jwt_invalid_base64_exception():
    token = "header.%%%$.signature"
    result = decode_jwt(token)
    assert result is None


def test_resend_verification_token_assignment():
    mock_user = {"id": "1", "username": "user", "email": "test@example.com", "emailVerified": False}

    with patch("app.app.keycloak_admin.get_users", return_value=[mock_user]), \
         patch("app.app.send_verification_email"), \
         patch("secrets.token_urlsafe", return_value="fixedtoken"):

        response = client.post("/resend-verification", json={"username": "user"})

        # Assert token assigned correctly
        assert verification_tokens["fixedtoken"] == "1"
        assert response.status_code == 200


# -----------------------------
# SignupData edge cases
# -----------------------------
def test_username_too_short_or_long():
    with pytest.raises(ValidationError):
        SignupData(username="ab", email="a@b.com", password="Password1!", first_name="John", last_name="Doe")
    with pytest.raises(ValidationError):
        SignupData(username="a"*21, email="a@b.com", password="Password1!", first_name="John", last_name="Doe")


def test_password_missing_requirements():
    with pytest.raises(ValidationError):
        SignupData(username="user1", email="a@b.com", password="PASSWORD1!", first_name="John", last_name="Doe")
    with pytest.raises(ValidationError):
        SignupData(username="user1", email="a@b.com", password="Password!", first_name="John", last_name="Doe")
    with pytest.raises(ValidationError):
        SignupData(username="user1", email="a@b.com", password="Password1", first_name="John", last_name="Doe")


def test_names_with_invalid_chars():
    with pytest.raises(ValidationError):
        SignupData(username="user1", email="a@b.com", password="Password1!", first_name="Jo3hn", last_name="Doe")
    with pytest.raises(ValidationError):
        SignupData(username="user1", email="a@b.com", password="Password1!", first_name="John", last_name="Do3e")


# -----------------------------
# Resend verification send email failure test
# -----------------------------
def test_resend_verification_send_email_failure():
    mock_user = {
        "id": "1",
        "username": "user",
        "email": "test@example.com",
        "emailVerified": False,
    }

    with patch("app.app.keycloak_admin.get_users", return_value=[mock_user]), \
         patch("app.app.send_verification_email", side_effect=Exception("SMTP error")):

        try:
            client.post("/resend-verification", json={"username": "user"})
            assert False, "Expected exception not raised"
        except Exception as e:
            assert "SMTP error" in str(e)


# -----------------------------
# validation_exception_handler no errors test
# -----------------------------
def test_validation_exception_handler_no_errors():
    request = Request(scope={"type": "http"})
    exc = RequestValidationError([])

    response = asyncio.run(validation_exception_handler(request, exc))
    assert response.status_code == 422

    body = json.loads(response.body.decode())
    assert body.get("status") == "error"
    assert isinstance(body.get("message"), dict)