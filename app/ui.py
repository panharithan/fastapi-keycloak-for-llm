from datetime import datetime
import gradio as gr
import requests
from .settings import BASE_URL, LOGIN_URL, DATE_TIME_FORMATE, MODEL
from .chat_history import format_message

def get_history_from_backend(username, token):
    """Fetch chat history from FastAPI instead of MongoDB directly"""
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
            print("❌ Failed to load history:", res.text)
            return []
    except Exception as e:
        print("⚠️ Exception while fetching history:", e)
        return []


def clear_user_history(username, token):
    """Clear chat history through backend"""
    if not token or not username:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.delete(f"{BASE_URL}/history", headers=headers)
        if res.status_code == 200:
            return []
        else:
            print("❌ Failed to clear history:", res.text)
            return []
    except Exception as e:
        print("⚠️ Exception while clearing history:", e)
        return []


def chat_with_model(message, history, username, token):
    if not token or not username:
        history.append(format_message("assistant", "⚠️ Please log in first!"))
        return "", history

    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.post(f"{BASE_URL}/chat", json={"prompt": message}, headers=headers)
        if res.status_code == 200:
            reply = res.json().get("response", "")
            now = datetime.utcnow().strftime(DATE_TIME_FORMATE)
            history.extend([
                format_message("user", message, now),
                format_message("assistant", reply, now),
            ])
        else:
            history.append(format_message("assistant", f"❌ Error: {res.text}"))
    except Exception as e:
        history.append(format_message("assistant", f"⚠️ Exception: {e}"))
    return "", history


def chat_with_model(message, history, username, token):
    if not token or not username:
        history.append({"role": "assistant", "content": "⚠️ Please log in first!"})
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
            history.append({"role": "assistant", "content": f"❌ Error: {res.text}"})
    except Exception as e:
        history.append({"role": "assistant", "content": f"⚠️ Exception: {e}"})
    return "", history


# -------------------------------
# Auth Functions
# -------------------------------
def backend_login(username, password):
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
    token, error = backend_login(username, password)
    if token:
        history = get_history_from_backend(username, token)
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            token,
            username,
            f"✅ Welcome back, {username}!",
            history,
        )
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            None,
            None,
            f"❌ {error}",
            [],
        )


def logout_action():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        None,
        None,
        "👋 Logged out.",
        [],
    )


def on_clear_click(username, token):
    return clear_user_history(username, token)


def restore_session(username):
    """Restore chat via backend when reloading"""
    if not username:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            None,
            None,
            "🔒 Please log in.",
            [],
        )
    # Try to load stored token from browser localStorage
    # (Gradio doesn’t persist across reloads automatically)
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        None,
        username,
        "🔒 Session expired. Please log in again.",
        [],
    )


# -------------------------------
# Gradio Interface
# -------------------------------
with gr.Blocks(title="Chat + Keycloak + MongoDB", theme="soft") as demo:
    gr.Markdown("# 🧠 Secure Chat App with Keycloak Login")

    token_state = gr.State(None)
    username_state = gr.State(None)

    # --- Auth section ---
    with gr.Group(visible=True) as auth_section:
        gr.Markdown("### 🔐 Login")
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")
        login_status = gr.Markdown()

    # --- Chat section ---
    with gr.Group(visible=False) as chat_section:
        gr.Markdown(f"### 💬 Chat - Model {MODEL}")
        chatbot = gr.Chatbot(type="messages")
        msg_box = gr.Textbox(label="Type your message...")
        with gr.Row():
            send_btn = gr.Button("Send")
            clear_btn = gr.Button("Clear Chat")
            logout_btn = gr.Button("Logout")

    # --- Button actions ---
    login_btn.click(
        fn=on_login_click,
        inputs=[username_input, password_input],
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
        js="""
        (username, password) => {
            localStorage.setItem('username', username);
            return [username, password];
        }
        """
    )

    send_btn.click(
        fn=chat_with_model,
        inputs=[msg_box, chatbot, username_state, token_state],
        outputs=[msg_box, chatbot],
    )

    clear_btn.click(
        fn=on_clear_click,
        inputs=[username_state, token_state],
        outputs=[chatbot],
    )

    logout_btn.click(
        fn=logout_action,
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
        js="() => { localStorage.clear(); }"
    )

    # ✅ Restore session (auto-login flow can be extended)
    demo.load(
        fn=restore_session,
        inputs=[username_state],
        outputs=[auth_section, chat_section, token_state, username_state, login_status, chatbot],
        js="""
        () => {
            const username = localStorage.getItem('username');
            return [username];
        }
        """
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
