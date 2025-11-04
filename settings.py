
from keycloak import KeycloakAdmin
import os
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# SMTP with Google Mail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Keycloak
keycloak_admin = KeycloakAdmin(
    server_url="http://localhost:8080/",
    username=os.getenv("KEYCLOAK_ADMIN_USERNAME"),
    password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_id="admin-cli",
    verify=True
)
KEYCLOAK_URL = "http://localhost:8080"
REALM = "llm"
ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
ENCRYPTION_ALGO = "RS256"
AUDIENCE="account" # keycloak

KEYCLOAK_TOKEN_URL = "http://localhost:8080/realms/llm/protocol/openid-connect/token"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# UI
API_URL = "http://localhost:8000/generate"
SIGNUP_URL = "http://localhost:8000/signup"
RESEND_URL = "http://localhost:8000/resend-verification"  # new backend endpoint

# LLM
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
