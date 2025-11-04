import secrets
import re
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from pydantic import BaseModel, EmailStr, field_validator
import gradio as gr
from keycloak_utils import verify_token
from llm import get_response
from email_utils import send_verification_email
from settings import keycloak_admin


# -------------------------------
# Validation Model
# -------------------------------
class SignupData(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str

    @field_validator("username")
    def validate_username(cls, v):
        if not re.match(r"^[A-Za-z0-9_]{3,20}$", v):
            raise ValueError("Username must be 3–20 chars and contain only letters, numbers, or underscores.")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

    @field_validator("first_name", "last_name")
    def validate_names(cls, v, info):
        field_name = info.field_name  # <-- get the name here
        if not re.match(r"^[A-Za-z]{2,30}$", v):
            raise ValueError(f"{field_name.replace('_', ' ').capitalize()} must be 2–30 letters (no digits or special symbols).")
        return v

# -------------------------------
# App Initialization
# -------------------------------
verification_tokens = {}
security = HTTPBearer()
app = FastAPI()


# -------------------------------
# Auth dependency
# -------------------------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.get("/secure-endpoint")
def secure_data(user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {user['preferred_username']}"}


# -------------------------------
# LLM Endpoint
# -------------------------------
class Prompt(BaseModel):
    text: str


@app.post("/generate")
async def generate_text(prompt: Prompt, user: dict = Depends(get_current_user)):
    result = get_response(prompt.text)
    return {"response": result}


# -------------------------------
# Signup Endpoint
# -------------------------------
@app.post("/signup")
def signup(data: SignupData = Body(...)):
    username = data.username
    email = data.email
    password = data.password

    keycloak_admin.realm_name = "llm"

    created = keycloak_admin.create_user({
        "username": username,
        "email": email,
        "enabled": True,
        "emailVerified": False,
        "firstName": data.first_name,
        "lastName": data.last_name,
        "credentials": [{"type": "password", "value": password, "temporary": False}],
        "requiredActions": []
    })

    # Extract user ID
    user_id = created.split("/")[-1] if isinstance(created, str) and created.startswith("/users/") else created

    # Confirm user exists
    users = keycloak_admin.get_users()
    if user_id not in [u['id'] for u in users]:
        raise HTTPException(status_code=500, detail="User not found after creation")

    # Assign basic_user role
    roles = keycloak_admin.get_realm_roles()
    basic_user_role = next((r for r in roles if r['name'] == 'basic_user'), None)
    if not basic_user_role:
        raise HTTPException(status_code=500, detail="Role 'basic_user' not found")

    keycloak_admin.assign_realm_roles(user_id, [basic_user_role])

    # Verification token
    token = secrets.token_urlsafe(32)
    verification_tokens[token] = user_id
    verify_url = f"http://localhost:8000/verify?token={token}"
    send_verification_email(email, verify_url)

    return {"message": "Signup successful! Please check your email to verify your account."}


@app.get("/verify")
def verify_email(token: str = Query(...)):
    if token not in verification_tokens:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = verification_tokens.pop(token)
    keycloak_admin.update_user(user_id=user_id, payload={"emailVerified": True})
    return {"message": "✅ Email verified successfully! You can now log in."}


@app.post("/resend-verification")
def resend_verification(username: str = Body(..., embed=True)):
    users = keycloak_admin.get_users(query={"username": username})
    if not users:
        raise HTTPException(status_code=404, detail="❌ User not found")

    user = next((u for u in users if u["username"].lower() == username.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="❌ User not found")

    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User does not have an email configured")

    if user.get("emailVerified", False):
        return {"message": "✅ Email is already verified."}

    token = secrets.token_urlsafe(32)
    verification_tokens[token] = user["id"]
    verify_url = f"http://localhost:8000/verify?token={token}"

    send_verification_email(email, verify_url)
    return {"message": f"📧 Verification email resent successfully to {email}!"}


@app.get("/")
def root():
    return {"message": "Ollama LLM API with Keycloak Auth is running!"}


# -------------------------------
# Friendly Validation Handler
# -------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        field = err.get("loc")[-1]
        msg = err.get("msg")
        errors[field] = msg
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({
            "status": "error",
            "message": errors
        }),
    )


# -------------------------------
# Gradio UI Mount
# -------------------------------
def greet(name):
    return f"Hello, {name}!"


gradio_app = gr.Interface(fn=greet, inputs="text", outputs="text")
app = gr.mount_gradio_app(app, gradio_app, path="/")

# Run: uvicorn app:app --reload --host 0.0.0.0 --port 8000