import gradio as gr
import os
import requests
from .keycloak_client import keycloak_login
from .settings import API_URL, SIGNUP_URL, BASE_URL
from .chat_history import format_message
from .utils.file_utils import extract_text_from_file, extract_file_content

# -------------------------------
# Send Message + Optional PDF
# -------------------------------
models_env = os.getenv("AVAILABLE_MODELS", "")
AVAILABLE_MODELS = [m.strip() for m in models_env.split(",") if m.strip()]

def send_message_or_pdf(message, history, token, model, uploaded_file=None):
    history = history or []
    if not token:
        history.append({"role": "assistant", "content": "⚠️ You must log in first!"})
        return "", history, None

    pdf_note = ""
    hidden_context = ""

    if uploaded_file:
        try:
            content = extract_file_content(uploaded_file)
            extracted_text = extract_text_from_file(content)

            filename = getattr(uploaded_file, "name", "uploaded file")

            if extracted_text:
                hidden_context = f"\n\n📄 [Attached File: {filename}]\n\n{extracted_text[:3000]}"
                pdf_note = f"📎 File '{filename}' uploaded and processed."
            else:
                pdf_note = f"❌ Couldn't read text from file '{filename}'."
        except Exception as e:
            pdf_note = f"❌ Error processing file: {e}"

    message_to_backend = message + hidden_context
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.post(API_URL, json={"text": message_to_backend, "model": model}, headers=headers)
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

    # Clear message input and file input
    return "", history, None


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
            return [
                format_message(
                    m["role"],
                    m["content"],
                    m.get("timestamp"),
                    m.get("model")  # <-- pass model here
                )
                for m in messages
            ]
        else:
            return []
    except Exception as e:
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


def process_uploaded_file(file):
    if not file:
        return None
    content = extract_text_from_file(file)
    return None
    # return f"✅ Extracted {len(content)} characters from {file.name}"


# -------------------------------
# Gradio UI
# -------------------------------
with gr.Blocks() as demo:
    demo.css = """
    .small-logout {
        padding: 2px 6px !important;
        font-size: 14px !important;
        min-width: fit-content !important;
        width: fit-content !important;
        display: inline-block !important;
        flex-grow: 0 !important;
    }
    .small-upload {
        padding: 4px 8px !important;
        font-size: 14px !important;
        height: 110px !important;  
        margin-top: 6px;
    }
    .small-upload input[type="file"]::file-selector-button {
        content: "Attach Document";
    }
    .compact-dropdown .wrap {
        width: auto !important;
        min-width: fit-content !important;
        display: inline-flex !important;
    }
    .compact-dropdown select {
        width: auto !important;
    }
    """

    with gr.Row():
        gr.Markdown("# 🧑‍💻 Keycloak Login & Chat + Document Upload 💬")
        logout_btn = gr.Button("Logout", visible=False, elem_classes=["small-logout"],)

    token_state = gr.State(None)

    # ------- Auth Section -------
    with gr.Group(visible=True) as auth_section:
        with gr.Tab("Login"):
            username_login = gr.Textbox(label="Username")
            password_login = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            resend_btn = gr.Button("Resend Verification Email", visible=False)
            login_status = gr.Markdown()

        with gr.Tab("Sign Up"):
            username_signup = gr.Textbox(label="Username")
            email_signup = gr.Textbox(label="Email")
            first_name_signup = gr.Textbox(label="First Name")
            last_name_signup = gr.Textbox(label="Last Name")
            password_signup = gr.Textbox(label="Password", type="password")
            signup_btn = gr.Button("Create Account")
            signup_status = gr.Markdown()

    # ------- Chat Section -------
    with gr.Group(visible=False) as chat_section:
        gr.Markdown("### Chat Interface")

        # ------- Model Selector -------
        model_selector = gr.Dropdown(
            choices=AVAILABLE_MODELS,
            value="llama3.2",
            label="Select LLM Model",
            elem_classes=["compact-dropdown"],
        )

        chatbot = gr.Chatbot(type="messages")

        msg = gr.Textbox(label="Message")

        with gr.Row():
            send_btn = gr.Button("Send")
            clear_btn = gr.Button("Clear Chat")

        file_input = gr.File(
            label="Upload Document (PDF, Word, Excel, etc.)",
            file_types=[".pdf", ".docx", ".xlsx", ".xls", ".txt", ".pptx", ".odt", ".rtf"],
            interactive=True,
            elem_classes=["small-upload"]
        )
        # Optional: preview extracted text length on file change (you can comment this out if not needed)
        file_input.change(fn=process_uploaded_file, inputs=file_input, outputs=None)

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
        inputs=[msg, chatbot, token_state, model_selector, file_input],
        # inputs=[msg, chatbot, token_state, model_selector, file_input],
        outputs=[msg, chatbot, file_input],  # Clear file input after send
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