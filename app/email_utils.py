import smtplib
from email.mime.text import MIMEText
from .settings import *

def send_verification_email(recipient_email, verification_link):
    subject = "Verify your account for LLM chat"
    body = f"Hi,\n\nPlease verify your account by clicking the link below:\n\n{verification_link}\n\nThank you!"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.set_debuglevel(1)  # <-- Enable debug output to console
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        print(f"Verification email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
