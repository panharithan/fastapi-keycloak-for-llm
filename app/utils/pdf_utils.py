# utils/pdf_utils.py
import io
from PyPDF2 import PdfReader
from ..settings import BASE_URL
import requests

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF file (bytes).
    Works even if uploaded through FastAPI.
    """
    text = ""
    try:
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"❌ Failed to extract text: {e}"


# -------------------------------
# PDF Upload
# -------------------------------
import requests

def upload_pdf_to_backend(pdf_file, token, history=None):
    """
    Upload a PDF to backend, extract text, summarize, and append response to chat history.
    Returns (response_dict, updated_history)
    """
    history = history or []
    headers = {"Authorization": f"Bearer {token}"}

    if not pdf_file:
        history.append({"role": "assistant", "content": "⚠️ No PDF selected."})
        return {"status": "error", "message": "No file selected."}, history

    try:
        files = {"file": open(pdf_file.name, "rb")}
        res = requests.post("http://localhost:8000/upload-pdf", files=files, headers=headers)

        if res.status_code == 200:
            data = res.json()
            msg = data.get("message", "✅ PDF uploaded successfully.")
            summary = data.get("summary", "")

            display_text = msg
            if summary:
                display_text += f"\n\n🧠 **Summary:** {summary}"

            history.append({
                "role": "assistant",
                "content": display_text
            })
            return data, history
        else:
            error_msg = f"❌ PDF upload failed: {res.text}"
            history.append({"role": "assistant", "content": error_msg})
            return {"status": "error", "message": error_msg}, history

    except Exception as e:
        err_text = f"❌ Exception during upload: {e}"
        history.append({"role": "assistant", "content": err_text})
        return {"status": "error", "message": str(e)}, history
