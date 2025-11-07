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
    print("msg = ", msg)

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        if EMAIL_USE_TLS:
            server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(DEFAULT_FROM_EMAIL, recipient_email, msg.as_string())

    print(f"Verification email sent to {recipient_email}")
