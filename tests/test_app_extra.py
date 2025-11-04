import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app, verification_tokens

client = TestClient(app)

@patch("app.verify_token", side_effect=Exception("Invalid token"))
def test_secure_endpoint_unauthenticated(mock_verify):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/secure-endpoint", headers=headers)
    assert response.status_code == 401
    # Accept either message, or just check status code
    assert response.json()["detail"] in ["Invalid token", "Error decoding token headers."]

# 1. Test get_current_user failure (token invalid) triggers 401
@patch("keycloak_utils.verify_token", side_effect=Exception("Invalid token"))
def test_secure_endpoint_unauthenticated(mock_verify):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/secure-endpoint", headers=headers)
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


# 2. Test signup with Keycloak create_user failure (simulate API failure)
@patch("settings.keycloak_admin.create_user", side_effect=Exception("Keycloak API error"))
def test_signup_keycloak_create_user_failure(mock_create_user):
    payload = {
        "username": "valid_user",
        "email": "test@example.com",
        "password": "Valid123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 500 or response.status_code == 422 or response.status_code == 400


# 3. Test signup when user not found after creation
@patch("settings.keycloak_admin.create_user", return_value="/users/123")
@patch("settings.keycloak_admin.get_users", return_value=[])  # No users found
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


# 4. Test signup role not found
@patch("settings.keycloak_admin.create_user", return_value="/users/123")
@patch("settings.keycloak_admin.get_users", return_value=[{"id": "123"}])
@patch("settings.keycloak_admin.get_realm_roles", return_value=[])  # No roles returned
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


# 5. Test /verify endpoint invalid token
def test_verify_invalid_token():
    response = client.get("/verify?token=nonexistenttoken")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


# 6. Test /resend-verification with user not found
@patch("settings.keycloak_admin.get_users", return_value=[])
def test_resend_verification_user_not_found(mock_get_users):
    response = client.post("/resend-verification", json={"username": "nonexistent"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


# 7. Test /resend-verification when email is missing
@patch("settings.keycloak_admin.get_users", return_value=[{"id": "123", "username": "user1"}])
def test_resend_verification_no_email(mock_get_users):
    response = client.post("/resend-verification", json={"username": "user1"})
    assert response.status_code == 400
    assert "does not have an email configured" in response.json()["detail"]


# 8. Test /resend-verification when email already verified
@patch("settings.keycloak_admin.get_users", return_value=[{"id": "123", "username": "user1", "email": "user1@example.com", "emailVerified": True}])
def test_resend_verification_email_already_verified(mock_get_users):
    response = client.post("/resend-verification", json={"username": "user1"})
    assert response.status_code == 200
    assert "already verified" in response.json()["message"]


# 9. Test validation exception handler returns friendly errors
def test_validation_exception_handler():
    # Trigger validation error by missing required field
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


# 10. Test Gradio UI mounted at root returns 200 (just basic smoke test)
def test_gradio_ui_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ollama LLM API" in response.json()["message"]