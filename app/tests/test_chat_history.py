import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.app import app
from app.chat_history import encrypt_message, decrypt_message


# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def mock_user():
    return {"preferred_username": "test_user"}


@pytest.fixture
def auth_header():
    # Dummy Bearer token for testing
    return {"Authorization": "Bearer test_token"}


@pytest.fixture(autouse=True)
def override_get_current_user(mock_user):
    """
    Override FastAPI dependency get_current_user
    so we don't get 401 during tests.
    """
    def fake_user():
        return mock_user

    app.dependency_overrides.clear()
    from app import app as app_module
    app.dependency_overrides[app_module.get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# -------------------------------
# Tests
# -------------------------------
@patch("app.app.get_response")
@patch("app.app.save_user_message")
@patch("app.app.get_user_history")
def test_chat_endpoint(
    mock_get_user_history,
    mock_save_user_message,
    mock_get_response,
    mock_user,
    auth_header
):
    mock_get_user_history.return_value = [
        {"role": "assistant", "content": "Hello, how can I help?"}
    ]
    mock_get_response.return_value = "This is a test response."

    payload = {"prompt": "Tell me a joke"}
    response = client.post("/chat", json=payload, headers=auth_header)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a test response."
    mock_save_user_message.assert_called()
    mock_get_user_history.assert_called_once()


@patch("app.app.get_user_history")
def test_get_history_endpoint(mock_get_user_history, mock_user, auth_header):
    mock_get_user_history.return_value = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello there!"}
    ]

    response = client.get("/history", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2


@patch("app.app.clear_history")
def test_clear_history_endpoint(mock_clear_history, mock_user, auth_header):
    response = client.delete("/history", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Chat history cleared successfully."
    mock_clear_history.assert_called_once()

def test_encrypt_message_returns_encrypted_string():
    """Ensure encrypt_message() returns a base64-encoded ciphertext"""
    text = "hello world"
    encrypted = encrypt_message(text)

    # Check type and that encryption actually changes the text
    assert isinstance(encrypted, str)
    assert encrypted != text

    # Fernet tokens typically contain '=' or '-'
    assert any(c in encrypted for c in ['=', '-', '_'])

def test_decrypt_message_returns_original_text():
    """Ensure decrypt_message() restores original text"""
    text = "test message"
    encrypted = encrypt_message(text)
    decrypted = decrypt_message(encrypted)

    assert decrypted == text

def test_decrypt_message_handles_unencrypted_input():
    """Backward compatibility: decrypt_message should return plaintext if not encrypted"""
    plain_text = "legacy unencrypted message"
    result = decrypt_message(plain_text)

    assert result == plain_text

def test_encryption_is_reversible_with_same_key():
    """Ensure encryption-decryption cycle works consistently with the same Fernet key"""
    samples = ["short", "with spaces", "symbols!@#", "123456"]
    for text in samples:
        token = encrypt_message(text)
        assert decrypt_message(token) == text

def test_invalid_token_does_not_raise_error():
    """Ensure decrypt_message gracefully handles invalid tokens"""
    invalid_token = "not-a-valid-fernet-token"
    result = decrypt_message(invalid_token)
    # Should not raise an exception, should return same input
    assert result == invalid_token
