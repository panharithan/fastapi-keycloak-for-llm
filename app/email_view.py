import smtplib
from email.mime.text import MIMEText
import app.settings

def send_verification_email(recipient_email, verification_link):
    subject = "Verify your account for LLM chat"
    body = f"Hi,\n\nPlease verify your account by clicking the link below:\n\n{verification_link}\n\nThank you!"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = recipient_email
    print("msg = ", msg)

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.DEFAULT_FROM_EMAIL, recipient_email, msg.as_string())

    print(f"Verification email sent to {recipient_email}")
