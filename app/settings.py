from keycloak import KeycloakAdmin
import os
from dotenv import load_dotenv
import pytz

load_dotenv()  # Load .env file

# --- Time & Format ---
DATE_TIME_FORMAT = os.getenv("DATE_TIME_FORMAT", "%d-%m-%Y %H:%M:%S")
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Berlin"))

# --- SMTP with Google Mail ---
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# --- Keycloak ---
KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_PORT = os.getenv("KEYCLOAK_PORT", "8080")
KEYCLOAK_URL = f"http://{KEYCLOAK_HOST}:{KEYCLOAK_PORT}"

KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "llm")
KEYCLOAK_ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN_USERNAME")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_URL,
    username=KEYCLOAK_ADMIN_USERNAME,
    password=KEYCLOAK_ADMIN_PASSWORD,
    realm_name=KEYCLOAK_REALM,
    client_id="admin-cli",
    verify=True
)

REALM = KEYCLOAK_REALM
ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
ENCRYPTION_ALGO = os.getenv("ENCRYPTION_ALGO", "RS256")
AUDIENCE = os.getenv("AUDIENCE", "account")

KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# --- URLs for UI and API ---
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/generate"
SIGNUP_URL = f"{BASE_URL}/signup"
LOGIN_URL = f"{BASE_URL}/login"
VERIFY_URL = f"{BASE_URL}/verify?token="
RESEND_VERIFY_URL = f"{BASE_URL}/resend-verification"
RESEND_URL = RESEND_VERIFY_URL  # alias


# LLM
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
MODEL = os.getenv("MODEL")
