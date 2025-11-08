import gradio as gr
import requests
from .keycloak_client import keycloak_login  # existing util returning (token, error)
from .settings import API_URL, SIGNUP_URL, BASE_URL
from datetime import datetime
from .chat_history import format_message

# -------------------------------
# Backend Chat Functions
# -------------------------------
def get_history_from_backend(username, token):
    """Fetch chat history from backend"""
    if not token or not username:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(f"{BASE_URL}/history", headers=headers)
        if res.status_code == 200:
            data = res.json()
            messages = data.get("messages", [])
            return [
                format_message(msg["role"], msg["content"], msg.get("timestamp"))
                for msg in messages
            ]
        else:
            print("Failed to load history:", res.text)
            return []
    except Exception as e:
        print("Exception while fetching history:", e)
        return []


def clear_user_history(username, token):
    """Clear chat history via backend"""
    if not token or not username:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.delete(f"{BASE_URL}/history", headers=headers)
        if res.status_code == 200:
            return []
        else:
            print("Failed to clear history:", res.text)
            return []
    except Exception as e:
        print("Exception while clearing history:", e)
        return []


def chat_with_model(message, history, token):
    """Send message to backend and update history"""
    history = history or []
    if not token:
        history.append({"role": "assistant", "content": "⚠️ You must log in first!"})
        return "", history

    headers = {"Authorization": f"Bearer {token}"}
    try:
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
    except Exception as e:
        history.append({"role": "assistant", "content": f"Exception: {e}"})
    return "", history


# -------------------------------
# Auth Functions
# -------------------------------
def on_login_click(username, password):
    token, error = keycloak_login(username, password)
    if token:
        history = get_history_from_backend(username, token)
        return (
            gr.update(visible=False),  # auth_section
            gr.update(visible=True),   # chat_section
            token,
            history,
            f"✅ Login successful! Welcome, {username}.",
            gr.update(visible=True),   # logout_btn visible
            gr.update(visible=False),  # resend_btn hidden on success
        )
    else:
        # Check if error is about unverified email
        show_resend = False
        if error and ("email is not verified" in error.lower() or "not verified" in error.lower()):
            show_resend = True
        
        return (
            gr.update(visible=True),   # auth_section
            gr.update(visible=False),  # chat_section
            None,
            [],
            f"❌ Login failed: {error}",
            gr.update(visible=False),  # logout_btn hidden
            gr.update(visible=show_resend),  # show resend_btn only if email not verified error
        )

def logout_action():
    return (
        gr.update(visible=True),    # auth_section
        gr.update(visible=False),   # chat_section
        None,
        [],                        # chatbot cleared
        "👋 Logged out.",           # login_status
        gr.update(visible=False),  # logout_btn hidden
        gr.update(visible=True),   # resend_btn visible on logout
    )

def logout_action():
    return (
        gr.update(visible=True),    # auth_section
        gr.update(visible=False),   # chat_section
        None,                      # token_state
        [],                        # chatbot
        "👋 Logged out.",           # login_status
        gr.update(visible=False),  # logout_btn (hide on logout)
    )


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

    return gr.update(visible=True), gr.update(visible=False), None, [], msg


def on_resend_click(username):
    if not username:
        return "⚠️ Please enter your username first."
    try:
        res = requests.post(f"{BASE_URL}/resend-verification", json={"username": username})
        if res.status_code == 200:
            msg = res.json().get("message", "✅ Verification email resent successfully.")
        else:
            msg = f"❌ Error: {res.status_code} - {res.text}"
    except Exception as e:
        msg = f"❌ Exception during resend: {e}"
    return msg


def on_clear_click(token):
    # clear_user_history expects username and token, but old code only tracks token
    # You can modify this if you want to pass username too.
    # Here we assume token enough to clear history.
    return []  # clearing chat history locally; backend clear can be implemented similarly

# -------------------------------
# Gradio UI
# -------------------------------
with gr.Blocks() as demo:

    demo.css = """
    .small-logout {
        padding: 2px 6px !important;
        font-size: 16px !important;
        min-width: auto !important;
        width: auto !important;
        height: auto !important;
    }
    """
    with gr.Row():
        gr.Markdown("# 🧑‍💻 Keycloak Login & Signup + Chat 💬", elem_id="page-title")
        logout_btn = gr.Button("Logout", scale=0, visible=False, elem_classes=["small-logout"])

    token_state = gr.State(None)

    # --- Auth Section ---
    with gr.Group(visible=True) as auth_section:
        with gr.Tab("🔐 Login"):
            username_login = gr.Textbox(label="Username")
            password_login = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            resend_btn = gr.Button("Resend Verification Email", visible=False)  # initially hidden
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
        clear_btn = gr.Button("Clear Chat")

    # --- Button bindings ---
    login_btn.click(
        fn=on_login_click,
        inputs=[username_login, password_login],
        outputs=[auth_section, chat_section, token_state, chatbot, login_status, logout_btn, resend_btn],
    )

    resend_btn.click(
        fn=on_resend_click,
        inputs=[username_login],
        outputs=[login_status],
    )

    signup_btn.click(
        fn=on_signup_click,
        inputs=[username_signup, password_signup, email_signup, first_name_signup, last_name_signup],
        outputs=[auth_section, chat_section, token_state, chatbot, signup_status],
    )

    send_btn.click(
        fn=chat_with_model,
        inputs=[msg, chatbot, token_state],
        outputs=[msg, chatbot],
    )

    clear_btn.click(
        fn=on_clear_click,
        inputs=[token_state],
        outputs=[chatbot],
    )

    logout_btn.click(
        fn=logout_action,
        outputs=[auth_section, chat_section, token_state, chatbot, login_status, logout_btn],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)