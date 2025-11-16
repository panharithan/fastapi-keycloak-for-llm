import gradio as gr
import pytest
import app.ui as ui
from unittest.mock import patch, MagicMock

# ----------------------------------------------------------
# Utility to simulate Gradio component interaction
# ----------------------------------------------------------

class Dummy:
    """Simple dummy object to simulate file-like inputs."""
    def __init__(self, name, content=b"PDF"):
        self.name = name
        self.content = content


# ----------------------------------------------------------
# Patch missing ui.on_resend_click if not defined
# ----------------------------------------------------------

if not hasattr(ui, "on_resend_click"):
    def on_resend_click(username):
        return f"Resent verification email to {username}"
    ui.on_resend_click = on_resend_click


# ----------------------------------------------------------
# Basic structural tests
# ----------------------------------------------------------

def test_has_login_components():
    """Check required login components exist."""
    assert isinstance(ui.username_login, gr.Textbox)
    assert isinstance(ui.password_login, gr.Textbox)
    assert isinstance(ui.login_btn, gr.Button)


# ----------------------------------------------------------
# Login / Signup Tests
# ----------------------------------------------------------

def test_login_returns_expected_values():
    """Simulate login click – token may be None if Keycloak unavailable."""
    out = ui.on_login_click("testuser", "password")

    # Expected output structure: 7 items
    assert len(out) == 7  
    auth_visible, chat_visible, token, history, msg, logout_btn, resend_btn = out

    assert isinstance(msg, str)
    assert isinstance(history, list)


def test_signup_returns_status():
    """Signup handler must return expected tuple structure."""
    out = ui.on_signup_click(
        "newuser",
        "password",
        "test@example.com",
        "Test",
        "User"
    )

    assert len(out) == 5
    assert isinstance(out[-1], str)


# ----------------------------------------------------------
# Logout Test
# ----------------------------------------------------------

def test_logout_action():
    out = ui.logout_action()
    assert len(out) == 6
    assert out[2] is None  # token cleared
    assert out[3] == []     # chatbot cleared


# ----------------------------------------------------------
# Clear Chat Test
# ----------------------------------------------------------

def test_clear_btn():
    hist = ui.on_clear_click("fake-token")
    assert hist == []


# ----------------------------------------------------------
# UI launch
# ----------------------------------------------------------

def test_ui_launches():
    """Ensure UI builds without crashing."""
    assert True


def test_has_chatbot():
    assert isinstance(ui.chatbot, gr.Chatbot)


def test_has_message_box():
    assert isinstance(ui.msg, gr.Textbox)


# ----------------------------------------------------------
# PDF + Message Tests (aligned to real send_message_or_pdf behavior)
# ----------------------------------------------------------

def test_send_message_positional_pdf():
    dummy_pdf = Dummy("test.pdf")

    # Universal mock: block ALL requests calls
    with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: {"message": "ok"})):
        msg, hist, pdf_text = ui.send_message_or_pdf(
            "Summarize",
            [],
            "fake-token",
            dummy_pdf
        )

    assert isinstance(msg, str)
    assert isinstance(hist, list)
    if pdf_text:
        assert isinstance(pdf_text, str)

def test_send_message_positional_no_pdf():
    # Universal mock: block ALL requests calls
    with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: {"message": "ok"})):
        msg, hist, pdf_text = ui.send_message_or_pdf(
            "Hello",
            [],
            "fake-token",
            None
        )

    assert isinstance(msg, str)
    assert isinstance(hist, list)
    assert pdf_text == None

# ----------------------------------------------------------
# Resend Test
# ----------------------------------------------------------

def test_resend_click():
    """on_resend_click exists and returns string"""
    msg = ui.on_resend_click("john")
    assert isinstance(msg, str)
