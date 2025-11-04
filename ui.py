import gradio as gr
import requests
from keycloak_client import keycloak_login  # existing util returning (token, error)
from settings import API_URL, SIGNUP_URL


# -------------------------------
# Chat function
# -------------------------------
def chat_with_model(message, history, token):
    history = history or []
    if not token:
        history.append({"role": "assistant", "content": "⚠️ You must log in first!"})
        return "", history

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(API_URL, json={"text": message}, headers=headers)
    if res.status_code == 200:
        response = res.json().get("response", "")
        history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ])
    else:
        history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"Error: {res.text}"},
        ])
    return "", history


# -------------------------------
# Login function
# -------------------------------
def on_login_click(username, password):
    token, error = keycloak_login(username, password)
    if token:
        return gr.update(visible=False), gr.update(visible=True), token, f"✅ Login successful! Welcome, {username}."
    else:
        return gr.update(visible=True), gr.update(visible=False), None, f"❌ Login failed: {error}"


# -------------------------------
# Logout function
# -------------------------------
def logout_action():
    return gr.update(visible=True), gr.update(visible=False), None, "👋 Logged out."


# -------------------------------
# Signup function
# -------------------------------
def on_signup_click(username, password, email, first_name, last_name):
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name
    }
    try:
        res = requests.post(SIGNUP_URL, json=payload)
        if res.status_code == 200:
            msg = res.json().get("message", "Signup successful! Please check your email.")
        else:
            msg = f"Error: {res.status_code} - {res.text}"
    except Exception as e:
        msg = f"Exception during signup: {e}"

    return gr.update(visible=True), gr.update(visible=False), None, msg


# -------------------------------
# Resend Verification Email function
# -------------------------------
def on_resend_click(username):
    if not username:
        return "⚠️ Please enter your username first."
    try:
        res = requests.post("http://localhost:8000/resend-verification", json={"username": username})
        if res.status_code == 200:
            msg = res.json().get("message", "✅ Verification email resent successfully.")
        else:
            msg = f"❌ Error: {res.status_code} - {res.text}"
    except Exception as e:
        msg = f"❌ Exception during resend: {e}"
    return msg


# -------------------------------
# Gradio UI
# -------------------------------
with gr.Blocks() as demo:
    gr.Markdown("# 🧑‍💻 Keycloak Login & Signup + Chat 💬")

    token_state = gr.State(None)

    # --- Auth Section ---
    with gr.Group(visible=True) as auth_section:
        with gr.Tabs():
            # --- Login Tab ---
            with gr.Tab("🔐 Login"):
                username_login = gr.Textbox(label="Username")
                password_login = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Login")
                resend_btn = gr.Button("Resend Verification Email")   # New feature
                login_status = gr.Markdown()

            # --- Signup Tab ---
            with gr.Tab("🆕 Sign Up"):
                username_signup = gr.Textbox(label="Username")
                email_signup = gr.Textbox(label="Email")
                first_name_signup = gr.Textbox(label="First Name")
                last_name_signup = gr.Textbox(label="Last Name")
                password_signup = gr.Textbox(label="Password", type="password")
                signup_btn = gr.Button("Create Account")
                signup_status = gr.Markdown()

    # --- Chat Section ---
    with gr.Group(visible=False) as chat_section:
        gr.Markdown("### Chat Interface")
        chatbot = gr.Chatbot(type="messages")
        msg = gr.Textbox(label="Message")
        send_btn = gr.Button("Send")
        logout_btn = gr.Button("Logout")

    # --- Button bindings ---
    login_btn.click(
        fn=on_login_click,
        inputs=[username_login, password_login],
        outputs=[auth_section, chat_section, token_state, login_status],
    )

    resend_btn.click(
        fn=on_resend_click,
        inputs=[username_login],
        outputs=[login_status],
    )

    signup_btn.click(
        fn=on_signup_click,
        inputs=[username_signup, password_signup, email_signup, first_name_signup, last_name_signup],
        outputs=[auth_section, chat_section, token_state, signup_status],
    )

    send_btn.click(
        fn=chat_with_model,
        inputs=[msg, chatbot, token_state],
        outputs=[msg, chatbot],
    )

    logout_btn.click(
        fn=logout_action,
        inputs=[],
        outputs=[auth_section, chat_section, token_state, login_status],
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
