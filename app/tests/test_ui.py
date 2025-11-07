import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app import ui  # Adjust to your actual import path

# Mocks for gradio update
class DummyUpdate:
    def __init__(self, visible=None):
        self.visible = visible

def dummy_update(visible=None):
    return DummyUpdate(visible=visible)

@pytest.fixture(autouse=True)
def patch_gradio_update(monkeypatch):
    monkeypatch.setattr(ui.gr, "update", dummy_update)
    yield


# ---------------------------
# Tests for get_history_from_backend
# ---------------------------
@patch("app.ui.requests.get")
def test_get_history_from_backend_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messages": [
            {"role": "user", "content": "Hello", "timestamp": "2025-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there"},
        ]
    }
    mock_get.return_value = mock_resp

    result = ui.get_history_from_backend("user", "token")
    assert isinstance(result, list)
    assert all("role" in m and "content" in m for m in result)


@patch("app.ui.requests.get")
def test_get_history_from_backend_failure_status(mock_get):
    mock_resp = MagicMock(status_code=500, text="Error")
    mock_get.return_value = mock_resp

    result = ui.get_history_from_backend("user", "token")
    assert result == []


@patch("app.ui.requests.get")
def test_get_history_from_backend_exception(mock_get):
    mock_get.side_effect = Exception("fail")

    result = ui.get_history_from_backend("user", "token")
    assert result == []


def test_get_history_from_backend_missing_params():
    assert ui.get_history_from_backend(None, "token") == []
    assert ui.get_history_from_backend("user", None) == []
    assert ui.get_history_from_backend(None, None) == []


# ---------------------------
# Tests for clear_user_history
# ---------------------------
@patch("app.ui.requests.delete")
def test_clear_user_history_success(mock_delete):
    mock_resp = MagicMock(status_code=200)
    mock_delete.return_value = mock_resp

    result = ui.clear_user_history("user", "token")
    assert result == []


@patch("app.ui.requests.delete")
def test_clear_user_history_fail_status(mock_delete):
    mock_resp = MagicMock(status_code=400, text="Fail")
    mock_delete.return_value = mock_resp

    result = ui.clear_user_history("user", "token")
    assert result == []


@patch("app.ui.requests.delete")
def test_clear_user_history_exception(mock_delete):
    mock_delete.side_effect = Exception("fail")

    result = ui.clear_user_history("user", "token")
    assert result == []


def test_clear_user_history_missing_params():
    assert ui.clear_user_history(None, "token") == []
    assert ui.clear_user_history("user", None) == []
    assert ui.clear_user_history(None, None) == []


# ---------------------------
# Tests for chat_with_model
# ---------------------------
@patch("app.ui.requests.post")
def test_chat_with_model_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Hello back!"}
    mock_post.return_value = mock_resp

    history = []
    message = "Hello"
    token = "token"
    username = "user"

    reply, updated_history = ui.chat_with_model(message, history, username, token)
    assert reply == ""
    assert any(m["content"] == "Hello" for m in updated_history or [])
    assert any(m["content"] == "Hello back!" for m in updated_history or [])


@patch("app.ui.requests.post")
def test_chat_with_model_fail_status(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad request"
    mock_post.return_value = mock_resp

    history = []
    message = "Hello"
    token = "token"
    username = "user"

    _, updated_history = ui.chat_with_model(message, history, username, token)
    assert any("❌ Error" in m["content"] for m in updated_history)


@patch("app.ui.requests.post")
def test_chat_with_model_exception(mock_post):
    mock_post.side_effect = Exception("fail")

    history = []
    message = "Hello"
    token = "token"
    username = "user"

    _, updated_history = ui.chat_with_model(message, history, username, token)
    assert any("⚠️ Exception" in m["content"] for m in updated_history)


def test_chat_with_model_missing_token_or_username():
    history = []
    reply, updated_history = ui.chat_with_model("msg", history, None, None)
    assert reply == ""
    assert any("Please log in" in m.get("content", "") for m in updated_history)


# ---------------------------
# Tests for backend_login
# ---------------------------
@patch("app.ui.requests.post")
def test_backend_login_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "token"}
    mock_post.return_value = mock_resp

    token, error = ui.backend_login("user", "pass")
    assert token == "token"
    assert error is None


@patch("app.ui.requests.post")
def test_backend_login_fail_status(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"detail": "Unauthorized"}
    mock_post.return_value = mock_resp

    token, error = ui.backend_login("user", "pass")
    assert token is None
    assert "Login failed" in error


@patch("app.ui.requests.post")
def test_backend_login_exception(mock_post):
    mock_post.side_effect = Exception("fail")

    token, error = ui.backend_login("user", "pass")
    assert token is None
    assert "fail" in error


# ---------------------------
# Tests for on_login_click
# ---------------------------
@patch("app.ui.get_history_from_backend")
@patch("app.ui.backend_login")
def test_on_login_click_success(mock_backend_login, mock_get_history):
    mock_backend_login.return_value = ("token", None)
    mock_get_history.return_value = [{"role": "assistant", "content": "Hi"}]

    auth_visible, chat_visible, token, username, status, history = ui.on_login_click("user", "pass")
    assert not auth_visible.visible
    assert chat_visible.visible
    assert token == "token"
    assert username == "user"
    assert "Welcome back" in status
    assert isinstance(history, list)


@patch("app.ui.backend_login")
def test_on_login_click_fail(mock_backend_login):
    mock_backend_login.return_value = (None, "error message")

    auth_visible, chat_visible, token, username, status, history = ui.on_login_click("user", "pass")
    assert auth_visible.visible
    assert not chat_visible.visible
    assert token is None
    assert username is None
    assert "❌" in status
    assert history == []


# ---------------------------
# Tests for logout_action
# ---------------------------
def test_logout_action():
    auth_visible, chat_visible, token, username, status, history = ui.logout_action()
    assert auth_visible.visible
    assert not chat_visible.visible
    assert token is None
    assert username is None
    assert "Logged out" in status
    assert history == []


# ---------------------------
# Tests for on_clear_click
# ---------------------------
@patch("app.ui.clear_user_history")
def test_on_clear_click(mock_clear_user_history):
    mock_clear_user_history.return_value = ["history cleared"]
    result = ui.on_clear_click("user", "token")
    assert result == ["history cleared"]


# ---------------------------
# Tests for restore_session
# ---------------------------
def test_restore_session_no_username():
    auth_visible, chat_visible, token, username, status, history = ui.restore_session(None)
    assert auth_visible.visible
    assert not chat_visible.visible
    assert token is None
    assert username is None
    assert "Please log in" in status
    assert history == []


def test_restore_session_with_username():
    auth_visible, chat_visible, token, username, status, history = ui.restore_session("user")
    assert auth_visible.visible
    assert not chat_visible.visible
    assert token is None
    assert username == "user"
    assert "Session expired" in status
    assert history == []