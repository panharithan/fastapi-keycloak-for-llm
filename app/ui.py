# ui.py
from datetime import datetime
import gradio as gr
import requests
from .settings import BASE_URL, LOGIN_URL, DATE_TIME_FORMATE, MODEL, SIGNUP_URL
from .chat_history import format_message

# -------------------------------
# Backend Chat Functions
# -------------------------------
def get_history_from_backend(username, token):
    """Fetch chat history from FastAPI backend"""
    if not token or not username:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(f"{BASE_URL}/history", headers=headers)
        if res.status_code == 200:
            data = res.json()
            messages = data.get("messages", [])
            return [
                format_message(
                    msg["role"],
                    msg["content"],
                    msg.get("timestamp", None),
                )
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


def chat_with_model(message, history, username, token):
    """Send message to backend and update history"""
    if not token or not username:
        history.append({"role": "assistant", "content": "Please log in first!"})
        return "", history

    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.post(f"{BASE_URL}/chat", json={"prompt": message}, headers=headers)
        if res.status_code == 200:
            reply = res.json().get("response", "")
            history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply},
            ])
        else:
            history.append({"role": "assistant", "content": f"Error: {res.text}"})
    except Exception as e:
        history.append({"role": "assistant", "content": f"Exception: {e}"})
    return "", history


# -------------------------------
# Auth Functions
# -------------------------------
def backend_login(username, password):
    """Login via backend"""
    try:
        res = requests.post(LOGIN_URL, json={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token"), None
        else:
            detail = res.json().get("detail", res.text)
            return None, f"Login failed: {detail}"
    except Exception as e:
        return None, str(e)


def on_login_click(username, password):
    """Handle login button click"""
    token, error = backend_login(username, password)
    if token:
        history = get_history_from_backend(username, token)
        return (
            gr.update(visible=False),  # auth_section
            gr.update(visible=True),   # chat_section
            token,                     # token_state
            username,                  # username_state
            f"Welcome back, {username}!",  # login_status
            history,                   # chatbot
        )
    else:
        return (
            gr.update(visible=True),   # auth_section
            gr.update(visible=False),  # chat_section
            None,                      # token_state
            None,                      # username_state
            f"Error: {error}",         # login_status
            [],                        # chatbot
        )


def on_signup_click(username, password, email, first_name, last_name):
    """Handle signup button click"""
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

    return (
        gr.update(visible=True),   # auth_section (stay on auth)
        gr.update(visible=False),  # chat_section
        None,                      # token_state
        None,                      # username_state
        msg,                       # signup_status
        [],                        # chatbot
    )


def on_resend_click(username):
    """Resend verification email"""
    if not username:
        return "Please enter your username first."
    try:
        res = requests.post(f"{BASE_URL}/resend-verification", json={"username": username})
        if res.status_code == 200:
            msg = res.json().get("message", "Verification email resent successfully.")
        else:
            msg = f"Error: {res.status_code} - {res.text}"
    except Exception as e:
        msg = f"Exception during resend: {e}"
    return msg


def logout_action():
    """Handle logout"""
    return (
        gr.update(visible=True),   # auth_section
        gr.update(visible=False),  # chat_section
        None,                      # token_state
        None,                      # username_state
        "Logged out.",             # status
        [],                        # chatbot
    )


def on_clear_click(username, token):
    """Clear chat history"""
    return clear_user_history(username, token)


def restore_session(username, token):
    """Restore chat session from localStorage"""
    print(f"[RESTORE] username={username}, token={token}")
    
    if not username or not token or username == "null" or token == "null":
        print("[RESTORE] No valid session found")
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            None,
            None,
            "Please log in.",
            [],
        )
    
    # Load chat history from backend
    history = get_history_from_backend(username, token)
    print(f"[RESTORE] Session restored for {username}")
    
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        token,
        username,
        f"Restored session for {username}",
        history,
    )


# -------------------------------
# Gradio Interface
# -------------------------------
with gr.Blocks(title="Chat + Keycloak + MongoDB", theme="soft") as demo:
    demo.css = """
        .neutral-label label {
            color: #555 !important;         /* Neutral gray */
            font-weight: 500 !important;    /* Medium weight for better readability */
        }
        """
    gr.Markdown("# Secure Chat App with Keycloak Login")

    # Hidden textboxes for localStorage values
    stored_username = gr.Textbox(visible=False, elem_id="stored_username")
    stored_token = gr.Textbox(visible=False, elem_id="stored_token")

    token_state = gr.State(None)
    username_state = gr.State(None)

    # --- Auth Section ---
    with gr.Group(visible=True) as auth_section:
        with gr.Tabs():
            # --- Login Tab ---
            with gr.Tab("Login"):
                gr.Markdown("### Login to your account")
                username_login = gr.Textbox(label="Username", elem_classes=["neutral-input"])
                password_login = gr.Textbox(label="Password", type="password", elem_classes=["neutral-input"])
                login_btn = gr.Button("Login", variant="secondary")
                resend_btn = gr.Button("Resend Verification Email")
                login_status = gr.Markdown()

            # --- Signup Tab ---
            with gr.Tab("Sign Up"):
                gr.Markdown("### Create a new account")
                username_signup = gr.Textbox(label="Username")
                email_signup = gr.Textbox(label="Email")
                first_name_signup = gr.Textbox(label="First Name")
                last_name_signup = gr.Textbox(label="Last Name")
                password_signup = gr.Textbox(label="Password", type="password")
                signup_btn = gr.Button("Create Account", variant="secondary")
                signup_status = gr.Markdown()

    # --- Chat Section ---
    with gr.Group(visible=False) as chat_section:
        gr.Markdown(f"### Chat - Model: {MODEL}")
        chatbot = gr.Chatbot(type="messages", height=500)
        msg_box = gr.Textbox(label="Type your message...", placeholder="Ask me anything...")
        with gr.Row():
            send_btn = gr.Button("Send", variant="secondary")
            clear_btn = gr.Button("Clear Chat")
            logout_btn = gr.Button("Logout")

    # --- Button Actions ---
    
    # Login
    login_btn.click(
        fn=on_login_click,
        inputs=[username_login, password_login],
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
    ).success(
        fn=None,
        inputs=[username_state, token_state],
        js="""
        (username, token) => {
            console.log('[SAVE] Saving credentials:', username, token);
            if (username && token) {
                localStorage.setItem('username', username);
                localStorage.setItem('token', token);
                console.log('[SAVE] Saved to localStorage!');
            }
        }
        """
    )

    # Resend verification
    resend_btn.click(
        fn=on_resend_click,
        inputs=[username_login],
        outputs=[login_status],
    )

    # Signup
    signup_btn.click(
        fn=on_signup_click,
        inputs=[username_signup, password_signup, email_signup, first_name_signup, last_name_signup],
        outputs=[auth_section, chat_section, token_state, username_state, signup_status, chatbot],
    )

    # Send message
    send_btn.click(
        fn=chat_with_model,
        inputs=[msg_box, chatbot, username_state, token_state],
        outputs=[msg_box, chatbot],
    )

    # Clear chat
    clear_btn.click(
        fn=on_clear_click,
        inputs=[username_state, token_state],
        outputs=[chatbot],
    )

    # Logout
    logout_btn.click(
        fn=logout_action,
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
    ).then(
        fn=None,
        inputs=None,
        outputs=None,
        js="""
        () => {
            localStorage.removeItem('username');
            localStorage.removeItem('token');
            console.log('[LOGOUT] Cleared localStorage');
        }
        """
    )

    # Restore session on page load
    demo.load(
        fn=None,
        inputs=None,
        outputs=[stored_username, stored_token],
        js="""
        () => {
            const username = localStorage.getItem('username') || '';
            const token = localStorage.getItem('token') || '';
            console.log('[LOAD] Loading from localStorage:', username, token);
            return [username, token];
        }
        """
    ).then(
        fn=restore_session,
        inputs=[stored_username, stored_token],
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)