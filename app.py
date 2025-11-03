# app.py
import secrets
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import gradio as gr
from pydantic import BaseModel
from keycloak_utils import verify_token  # Your token validation utility
from llm import get_response  # Your existing LLM connection function
from email_utils import send_verification_email
from settings import keycloak_admin

class SignupData(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str


verification_tokens = {}
security = HTTPBearer()
app = FastAPI()

# Auth dependency to validate Keycloak token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = verify_token(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

# Secure test endpoint
@app.get("/secure-endpoint")
def secure_data(user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {user['preferred_username']}"}

# LLM prompt schema
class Prompt(BaseModel):
    text: str

# Protected LLM generate endpoint
@app.post("/generate")
async def generate_text(prompt: Prompt, user: dict = Depends(get_current_user)):
    # You have user info here if needed (user['preferred_username'], roles, etc)
    result = get_response(prompt.text)
    return {"response": result}

@app.post("/signup")
def signup(data: SignupData = Body(...)):
    username = data.username
    email = data.email
    password = data.password

    print(f"Signup called with username={username}, email={email}")
    keycloak_admin.realm_name = "llm"  # Ensure correct realm

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

    # Extract user_id
    if isinstance(created, str) and created.startswith("/users/"):
        user_id = created.split("/")[-1]
    else:
        user_id = created

    print(f"User created with id {user_id}")

    # Confirm user exists
    users = keycloak_admin.get_users()
    print(f"Users in realm: {[u['id'] for u in users]}")
    if user_id not in [u['id'] for u in users]:
        raise HTTPException(status_code=500, detail="User not found after creation")

    # Get group
    groups = keycloak_admin.get_groups()
    basic_user_group = next((g for g in groups if g['name'] == 'basic_user'), None)
    if not basic_user_group:
        raise HTTPException(status_code=500, detail="Group 'basic_user' not found")

    print(f"Adding user {user_id} to group {basic_user_group['name']} (id: {basic_user_group['id']})")

    # # Add user to group
    # keycloak_admin.group_user_add(basic_user_group['id'], user_id)
    # print(f"User {user_id} added to group 'basic_user'")

    # Assign role
    roles = keycloak_admin.get_realm_roles()
    basic_user_role = next((r for r in roles if r['name'] == 'basic_user'), None)
    if not basic_user_role:
        raise HTTPException(status_code=500, detail="Role 'basic_user' not found")

    keycloak_admin.assign_realm_roles(user_id, [basic_user_role])
    print(f"Role 'basic_user' assigned to user {user_id}")

    # Verification token & email
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

"""
Email Token life time settins in keycloak:
->Override just the Email Verification
1. Go to "llm" realm or your realm name and choose "Realm Settings"
2. Scroll down to "Tokens" tab
3. Override Action Tokens
Find Email Verification
Enter your desired time (e.g. 1440 minutes = 24 hours)
4. Save changes
"""
@app.post("/resend-verification")
def resend_verification(username: str = Body(..., embed=True)):
    """Resend the verification email using username."""
    users = keycloak_admin.get_users(query={"username": username})
    if not users:
        raise HTTPException(status_code=404, detail="❌ User not found")

    # Find matching user (some realms return multiple)
    user = next((u for u in users if u["username"].lower() == username.lower()), None)
    if not user:
        raise HTTPException(status_code=404, detail="❌ User not found")

    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="User does not have an email configured")

    if user.get("emailVerified", False):
        return {"message": "✅ Email is already verified."}

    # Generate a new token and store mapping
    token = secrets.token_urlsafe(32)
    verification_tokens[token] = user["id"]
    verify_url = f"http://localhost:8000/verify?token={token}"

    send_verification_email(email, verify_url)
    return {"message": f"📧 Verification email resent successfully to {email}!"}

@app.get("/")
def root():
    print("Welcoome ----- ")
    return {"message": "Ollama LLM API with Keycloak Auth is running!"}

# Gradio UI function
def greet(name):
    return f"Hello, {name}!"

# Mount Gradio app at root ("/") - Note: this is unprotected for demonstration
gradio_app = gr.Interface(fn=greet, inputs="text", outputs="text")
app = gr.mount_gradio_app(app, gradio_app, path="/")

# Run with:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
