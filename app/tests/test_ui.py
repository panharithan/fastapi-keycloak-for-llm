import pytest
from unittest.mock import patch, MagicMock
from app import ui

# Dummy update function to mock gr.update
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

    reply, updated_history = ui.chat_with_model(message, history, token)
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

    _, updated_history = ui.chat_with_model(message, history, token)
    assert any("Error" in m["content"] for m in updated_history)


@patch("app.ui.requests.post")
def test_chat_with_model_exception(mock_post):
    mock_post.side_effect = Exception("fail")

    history = []
    message = "Hello"
    token = "token"

    _, updated_history = ui.chat_with_model(message, history, token)
    assert any("Exception" in m["content"] for m in updated_history)


def test_chat_with_model_missing_token():
    history = []
    reply, updated_history = ui.chat_with_model("msg", history, None)
    assert reply == ""
    assert any("You must log in" in m.get("content", "") for m in updated_history)


# ---------------------------
# Tests for on_login_click
# ---------------------------
@patch("app.ui.keycloak_login")
@patch("app.ui.get_history_from_backend")
def test_on_login_click_success(mock_get_history, mock_keycloak_login):
    mock_keycloak_login.return_value = ("token", None)
    mock_get_history.return_value = [{"role": "assistant", "content": "Hi"}]

    outputs = ui.on_login_click("user", "pass")
    auth_section, chat_section, token, chatbot, login_status, logout_btn, resend_btn = outputs

    assert isinstance(auth_section, DummyUpdate)
    assert not auth_section.visible
    assert isinstance(chat_section, DummyUpdate)
    assert chat_section.visible
    assert token == "token"
    assert isinstance(chatbot, list)
    assert "Login successful" in login_status
    assert isinstance(logout_btn, DummyUpdate)
    assert logout_btn.visible
    assert isinstance(resend_btn, DummyUpdate)
    assert not resend_btn.visible


@patch("app.ui.keycloak_login")
def test_on_login_click_fail_email_not_verified(mock_keycloak_login):
    error_msg = "Email is not verified"
    mock_keycloak_login.return_value = (None, error_msg)

    outputs = ui.on_login_click("user", "pass")
    auth_section, chat_section, token, chatbot, login_status, logout_btn, resend_btn = outputs

    assert isinstance(auth_section, DummyUpdate)
    assert auth_section.visible
    assert isinstance(chat_section, DummyUpdate)
    assert not chat_section.visible
    assert token is None
    assert chatbot == []
    assert "Login failed" in login_status
    assert isinstance(logout_btn, DummyUpdate)
    assert not logout_btn.visible
    assert isinstance(resend_btn, DummyUpdate)
    assert resend_btn.visible


@patch("app.ui.keycloak_login")
def test_on_login_click_fail_other_error(mock_keycloak_login):
    error_msg = "Wrong password"
    mock_keycloak_login.return_value = (None, error_msg)

    outputs = ui.on_login_click("user", "pass")
    auth_section, chat_section, token, chatbot, login_status, logout_btn, resend_btn = outputs

    assert auth_section.visible
    assert not chat_section.visible
    assert token is None
    assert chatbot == []
    assert "Login failed" in login_status
    assert not logout_btn.visible
    assert not resend_btn.visible


# ---------------------------
# Tests for logout_action
# ---------------------------
def test_logout_action():
    outputs = ui.logout_action()
    auth_section, chat_section, token, chatbot, login_status, logout_btn = outputs

    assert auth_section.visible
    assert not chat_section.visible
    assert token is None
    assert chatbot == []
    assert "Logged out" in login_status
    assert not logout_btn.visible


# ---------------------------
# Tests for on_signup_click
# ---------------------------
@patch("app.ui.requests.post")
def test_on_signup_click_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": "Check your email"}
    mock_post.return_value = mock_resp

    outputs = ui.on_signup_click("user", "pass", "email@test.com", "First", "Last")
    auth_section, chat_section, token, chatbot, signup_status = outputs

    assert auth_section.visible
    assert not chat_section.visible
    assert token is None
    assert chatbot == []
    assert "Check your email" in signup_status


@patch("app.ui.requests.post")
def test_on_signup_click_fail_status(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad request"
    mock_post.return_value = mock_resp

    outputs = ui.on_signup_click("user", "pass", "email@test.com", "First", "Last")
    _, _, _, _, signup_status = outputs

    assert "Error" in signup_status


@patch("app.ui.requests.post")
def test_on_signup_click_exception(mock_post):
    mock_post.side_effect = Exception("fail")

    outputs = ui.on_signup_click("user", "pass", "email@test.com", "First", "Last")
    _, _, _, _, signup_status = outputs

    assert "Exception" in signup_status


# ---------------------------
# Tests for on_resend_click
# ---------------------------
@patch("app.ui.requests.post")
def test_on_resend_click_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": "Email resent"}
    mock_post.return_value = mock_resp

    msg = ui.on_resend_click("user")
    assert "Verification email resent" in msg or "Email resent" in msg


@patch("app.ui.requests.post")
def test_on_resend_click_fail_status(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Error"
    mock_post.return_value = mock_resp

    msg = ui.on_resend_click("user")
    assert "Error" in msg


@patch("app.ui.requests.post")
def test_on_resend_click_exception(mock_post):
    mock_post.side_effect = Exception("fail")

    msg = ui.on_resend_click("user")
    assert "Exception" in msg


def test_on_resend_click_no_username():
    msg = ui.on_resend_click("")
    assert "Please enter your username" in msg


# ---------------------------
# Tests for on_clear_click
# ---------------------------
def test_on_clear_click():
    result = ui.on_clear_click("token")
    assert result == []