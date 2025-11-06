from fastapi.testclient import TestClient
from unittest.mock import patch
from app.app import app  # Import app instance from app.app

client = TestClient(app)

@patch("app.app.keycloak_admin.get_users")
@patch("app.app.send_verification_email")
def test_resend_verification_success(mock_send, mock_get_users):
    mock_get_users.return_value = [{
        "id": "123",
        "username": "user1",
        "email": "user1@example.com",
        "emailVerified": False,
    }]
    response = client.post("/resend-verification", json={"username": "user1"})
    assert response.status_code == 200
    assert "resent successfully" in response.json()["message"]
    mock_send.assert_called_once()

@patch("app.app.keycloak_admin.get_users", return_value=[])
def test_resend_verification_user_not_found(mock_get):
    response = client.post("/resend-verification", json={"username": "ghost"})
    assert response.status_code == 404