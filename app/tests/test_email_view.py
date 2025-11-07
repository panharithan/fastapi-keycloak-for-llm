import pytest
from unittest.mock import patch, MagicMock
import app.email_view  # Adjust import if your module name differs

@patch("app.email_view.smtplib.SMTP")
@patch("app.email_view.DEFAULT_FROM_EMAIL", "no-reply@example.com")
@patch("app.email_view.EMAIL_HOST", "smtp.example.com")
@patch("app.email_view.EMAIL_PORT", 587)
@patch("app.email_view.EMAIL_USE_TLS", True)
@patch("app.email_view.EMAIL_HOST_USER", "user@example.com")
@patch("app.email_view.EMAIL_HOST_PASSWORD", "password123")
def test_send_verification_email(mock_smtp_class):
    # Mock the SMTP instance and context manager
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    recipient = "recipient@example.com"
    verification_link = "https://example.com/verify?token=abc123"

    app.email_view.send_verification_email(recipient, verification_link)

    # Check SMTP connection created with correct host and port
    mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
    # TLS started
    mock_smtp_instance.starttls.assert_called_once()
    # Login called with credentials
    mock_smtp_instance.login.assert_called_once_with("user@example.com", "password123")
    # Email sent with correct args
    mock_smtp_instance.sendmail.assert_called_once()
    args, _ = mock_smtp_instance.sendmail.call_args
    assert args[0] == "no-reply@example.com"
    assert args[1] == recipient
    assert "Verify your account for LLM chat" in args[2]


@patch("app.email_view.smtplib.SMTP")
@patch("app.email_view.DEFAULT_FROM_EMAIL", "no-reply@example.com")
@patch("app.email_view.EMAIL_HOST", "smtp.example.com")
@patch("app.email_view.EMAIL_PORT", 25)
@patch("app.email_view.EMAIL_USE_TLS", False)
@patch("app.email_view.EMAIL_HOST_USER", "user@example.com")
@patch("app.email_view.EMAIL_HOST_PASSWORD", "password123")
def test_send_verification_email_without_tls(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    recipient = "recipient@example.com"
    verification_link = "https://example.com/verify?token=abc123"

    app.email_view.send_verification_email(recipient, verification_link)

    mock_smtp_class.assert_called_once_with("smtp.example.com", 25)
    mock_smtp_instance.starttls.assert_not_called()
    mock_smtp_instance.login.assert_called_once_with("user@example.com", "password123")
    mock_smtp_instance.sendmail.assert_called_once()