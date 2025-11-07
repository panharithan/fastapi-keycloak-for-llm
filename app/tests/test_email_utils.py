import pytest
from unittest.mock import patch, MagicMock
import app.email_utils  # Adjust this to your actual module path

@patch("app.email_utils.smtplib.SMTP")
@patch("app.email_utils.DEFAULT_FROM_EMAIL", "no-reply@example.com")
@patch("app.email_utils.EMAIL_HOST", "smtp.example.com")
@patch("app.email_utils.EMAIL_PORT", 587)
@patch("app.email_utils.EMAIL_HOST_USER", "user@example.com")
@patch("app.email_utils.EMAIL_HOST_PASSWORD", "password123")
def test_send_verification_email_success(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    recipient = "recipient@example.com"
    verification_link = "https://example.com/verify?token=abc123"

    app.email_utils.send_verification_email(recipient, verification_link)

    # Check SMTP connection called correctly
    mock_smtp_class.assert_called_once_with("smtp.example.com", 587)

    # Check debug level set
    mock_smtp_instance.set_debuglevel.assert_called_once_with(1)

    # Check TLS started
    mock_smtp_instance.starttls.assert_called_once()

    # Check login credentials
    mock_smtp_instance.login.assert_called_once_with("user@example.com", "password123")

    # Check send_message called once with MIMEText message
    mock_smtp_instance.send_message.assert_called_once()
    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert recipient in sent_msg['To']
    assert sent_msg['From'] == "no-reply@example.com"
    assert "Verify your account for LLM chat" in sent_msg['Subject']


@patch("app.email_utils.smtplib.SMTP")
@patch("app.email_utils.DEFAULT_FROM_EMAIL", "no-reply@example.com")
@patch("app.email_utils.EMAIL_HOST", "smtp.example.com")
@patch("app.email_utils.EMAIL_PORT", 587)
@patch("app.email_utils.EMAIL_HOST_USER", "user@example.com")
@patch("app.email_utils.EMAIL_HOST_PASSWORD", "password123")
def test_send_verification_email_failure(mock_smtp_class, capsys):
    # Configure the SMTP mock to raise an exception on send_message
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.send_message.side_effect = Exception("SMTP send error")
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

    recipient = "recipient@example.com"
    verification_link = "https://example.com/verify?token=abc123"

    app.email_utils.send_verification_email(recipient, verification_link)

    # Capture stdout to check for error print statement
    captured = capsys.readouterr()
    assert "Failed to send email: SMTP send error" in captured.out