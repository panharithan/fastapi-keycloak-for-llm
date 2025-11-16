# app.py
import secrets
import re
import base64
import json
import requests
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from pydantic import BaseModel, EmailStr, field_validator

import gradio as gr
from .keycloak_utils import verify_token
from .llm import get_response
from .email_utils import send_verification_email
from .settings import keycloak_admin, PUBLIC_BASE_URL, KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET, KEYCLOAK_TOKEN_URL
from .chat_history import get_user_history, save_user_message, clear_history
from .utils.file_utils import extract_text_from_file

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
        field_name = info.field_name
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

def get_authenticated_username(user: dict) -> str:
    """
    Extracts and validates the preferred_username from the authenticated user.
    Raises HTTP 401 if the username is missing.
    """
    username = user.get("preferred_username")
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized user")
    return username

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.get("/secure-endpoint")
def secure_data(user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {user['preferred_username']}"}


# -------------------------------
# LLM Endpoint
# -------------------------------

def summarize_text(text: str, max_len: int = 1000):
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."

class Prompt(BaseModel):
    text: str
    model:str

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """
    Extract full text from PDF, summarize, and store to MongoDB
    as part of the user’s chat history (role='system').
    """
    username = get_authenticated_username(user)

    # 1️⃣ Extract text
    content = await file.read()
    pdf_text = extract_text_from_file(content)

    if not pdf_text:
        return {"status": "error", "message": "❌ No readable text found in PDF."}

    # 2️⃣ Save extracted text as context
    pdf_content_entry = f"[PDF Uploaded: {file.filename}]\n\n{pdf_text[:3000]}"
    save_user_message(username, "system", pdf_content_entry)

    # 3️⃣ Summarize
    summary = summarize_text(pdf_text)

    # 4️⃣ Optional: append summary to DB too
    save_user_message(username, "assistant", f"📄 Summary of {file.filename}:\n{summary}")

    # 5️⃣ Return success
    return {
        "status": "success",
        "message": f"✅ PDF '{file.filename}' processed and added to your context.",
        "summary": summary,
    }


@app.post("/generate")
async def generate_text(prompt: Prompt, user: dict = Depends(get_current_user)):
    username = get_authenticated_username(user)

    # Call LLM kernel
    result = get_response(prompt.text, prompt.model)

    # Save user and assistant messages
    save_user_message(username, "user", prompt.text)
    save_user_message(username, "assistant", result, prompt.model)

    return {"response": result}


# -------------------------------
# JWT Decode Helper
# -------------------------------
def decode_jwt(token: str):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        padding = '=' * (-len(payload) % 4)
        payload += padding
        decoded_bytes = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_bytes)
    except Exception as e:
        print(f"Failed to decode JWT: {e}")
        return None


# -------------------------------
# Login Endpoint (with verified email check)
# -------------------------------
class LoginData(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(data: LoginData = Body(...)):
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": data.username,
        "password": data.password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(KEYCLOAK_TOKEN_URL, data=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid username or password. Keycloak says: {response.text}"
        )

    token_data = response.json()
    access_token = token_data.get("access_token")

    # Verify email_verified via userinfo endpoint
    userinfo_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_resp = requests.get(userinfo_url, headers=headers)

    if userinfo_resp.status_code == 200:
        userinfo = userinfo_resp.json()
        print("Userinfo response:", userinfo)

        email_verified = userinfo.get("email_verified")
        if email_verified is None:
            print("⚠️ Warning: 'email_verified' not present in userinfo. Check Keycloak mappers/scopes.")
        elif not email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email is not verified. Please verify your email first."
            )
    else:
        print("⚠️ Userinfo request failed. Falling back to JWT decode.")
        claims = decode_jwt(access_token)
        print("Decoded claims:", claims)
        if not claims or not claims.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email is not verified"
            )

    return {
        "access_token": access_token,
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type"),
        "expires_in": token_data.get("expires_in")
    }


# -------------------------------
# Signup Endpoint
# -------------------------------
@app.post("/signup")
def signup(data: SignupData = Body(...)):
    username = data.username
    email = data.email
    password = data.password

    keycloak_admin.realm_name = REALM

    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")

    user_id = created.split("/")[-1] if isinstance(created, str) and created.startswith("/users/") else created

    users = keycloak_admin.get_users()
    if user_id not in [u['id'] for u in users]:
        raise HTTPException(status_code=500, detail="User not found after creation")

    roles = keycloak_admin.get_realm_roles()
    basic_user_role = next((r for r in roles if r['name'] == 'basic_user'), None)
    if not basic_user_role:
        raise HTTPException(status_code=500, detail="Role 'basic_user' not found")

    keycloak_admin.assign_realm_roles(user_id, [basic_user_role])

    token = secrets.token_urlsafe(32)
    verification_tokens[token] = user_id
    verify_url = f"{PUBLIC_BASE_URL}/verify?token={token}"
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
    users = keycloak_admin.get_users()
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
    verify_url = f"{PUBLIC_BASE_URL}/verify?token={token}"
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
# -------------------------------
# Chat History (Stable rollback)
# -------------------------------
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def chat(data: ChatRequest, user: dict = Depends(get_current_user)):
    username = get_authenticated_username(user)
    prompt = data.prompt

    # 🧠 Load chat history from MongoDB
    history = get_user_history(username)

    # 🧩 Build context for the model
    conversation = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in history[-10:]]
    )
    full_prompt = f"{conversation}\nUser: {prompt}"

    # 🦙 Call LLM to generate response
    reply = get_response(full_prompt)

    # 💾 Save user and assistant messages in MongoDB
    save_user_message(username, "user", prompt)
    save_user_message(username, "assistant", reply)

    return {"response": reply}


@app.get("/history")
def get_history(user: dict = Depends(get_current_user)):
    # Fetch chat history for the logged-in user
    username = get_authenticated_username(user)
    messages = get_user_history(username)
    return {"messages": messages}


@app.delete("/history")
def clear_user_history(user: dict = Depends(get_current_user)):
    # ✅ Clear chat history for the logged-in user
    username = get_authenticated_username(user)
    clear_history(username)
    return {"message": "Chat history cleared successfully."}


gradio_app = gr.Interface(fn=greet, inputs="text", outputs="text")
app = gr.mount_gradio_app(app, gradio_app, path="/")

# Run with:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
