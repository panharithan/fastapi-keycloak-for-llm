import gradio as gr
import requests
from .keycloak_client import keycloak_login
from .settings import API_URL, SIGNUP_URL, BASE_URL
from .chat_history import format_message
from .utils.pdf_utils import upload_pdf_to_backend, extract_text_from_pdf

# -------------------------------
# Combined Send Logic
# -------------------------------
def send_message_or_pdf(message, history, token, pdf_file=None):
    """Handle both normal messages and PDF uploads."""
    history = history or []
    if not token:
        history.append({"role": "assistant", "content": "⚠️ You must log in first!"})
        return "", history

    pdf_note = ""
    hidden_context = ""

    # --- Handle PDF attachment ---
    if pdf_file:
        try:
            with open(pdf_file.name, "rb") as f:
                pdf_content = f.read()
            extracted_text = extract_text_from_pdf(pdf_content)

            if extracted_text:
                hidden_context = f"\n\n📄 [Attached PDF: {pdf_file.name}]\n\n{extracted_text[:3000]}"
                pdf_note = f"📎 PDF '{pdf_file.name}' uploaded and processed."
            else:
                pdf_note = f"❌ Couldn't read text from PDF '{pdf_file.name}'."
        except Exception as e:
            pdf_note = f"❌ Error processing PDF: {e}"

    message_to_backend = message + hidden_context
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.post(API_URL, json={"text": message_to_backend}, headers=headers)
        if res.status_code == 200:
            response = res.json().get("response", "")
            display_msg = message if not pdf_note else f"{message}\n\n{pdf_note}"
            history.extend([
                {"role": "user", "content": display_msg},
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
# Auth & Utility Functions
# -------------------------------
def get_history_from_backend(username, token):
    if not token or not username:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(f"{BASE_URL}/history", headers=headers)
        if res.status_code == 200:
            data = res.json()
            messages = data.get("messages", [])
            return [format_message(m["role"], m["content"], m.get("timestamp")) for m in messages]
        else:
            print("Failed to load history:", res.text)
            return []
    except Exception as e:
        print("Exception while fetching history:", e)
        return []


def on_login_click(username, password):
    token, error = keycloak_login(username, password)
    if token:
        history = get_history_from_backend(username, token)
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            token,
            history,
            f"✅ Login successful! Welcome, {username}.",
            gr.update(visible=True),
            gr.update(visible=False),
        )
    else:
        show_resend = error and ("not verified" in error.lower())
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            None,
            [],
            f"❌ Login failed: {error}",
            gr.update(visible=False),
            gr.update(visible=show_resend),
        )


def logout_action():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        None,
        [],
        "👋 Logged out.",
        gr.update(visible=False),
    )


def on_signup_click(username, password, email, first_name, last_name):
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
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


def on_clear_click(token):
    return []


# -------------------------------
# Gradio UI
# -------------------------------
with gr.Blocks() as demo:
    demo.css = """
    .small-logout {
        padding: 2px 6px !important;
        font-size: 16px !important;
        min-width: auto !important;
    }
    .small-upload {
        padding: 4px 8px !important;
        font-size: 14px !important;
        height: 110px !important;  
        margin-top: 6px;
    }
    .small-upload input[type="file"]::file-selector-button {
        content: "Attach PDF";
    }
    """

    with gr.Row():
        gr.Markdown("# 🧑‍💻 Keycloak Login & Chat + PDF Upload 💬", elem_id="page-title")
        logout_btn = gr.Button("Logout", visible=False, elem_classes=["small-logout"])

    token_state = gr.State(None)

    # --- Authentication Section ---
    with gr.Group(visible=True) as auth_section:
        with gr.Tab("🔐 Login"):
            username_login = gr.Textbox(label="Username")
            password_login = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            resend_btn = gr.Button("Resend Verification Email", visible=False)
            login_status = gr.Markdown()

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

        msg = gr.Textbox(label="💬 Message", placeholder="Type your message here...")

        with gr.Row():
            send_btn = gr.Button("Send", scale=1)
            clear_btn = gr.Button("Clear Chat", scale=1)

        # 📎 Small upload button below Send
        pdf_file = gr.File(
            label="Upload PDF (optional)",
            file_types=[".pdf"],
            interactive=True,
            elem_classes=["small-upload"]
        )

    # --- Button Bindings ---
    login_btn.click(
        fn=on_login_click,
        inputs=[username_login, password_login],
        outputs=[auth_section, chat_section, token_state, chatbot, login_status, logout_btn, resend_btn],
    )

    signup_btn.click(
        fn=on_signup_click,
        inputs=[username_signup, password_signup, email_signup, first_name_signup, last_name_signup],
        outputs=[auth_section, chat_section, token_state, chatbot, signup_status],
    )

    send_btn.click(
        fn=send_message_or_pdf,
        inputs=[msg, chatbot, token_state, pdf_file],
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
