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
def upload_pdf_to_backend(pdf_file, token, history):
    """Upload a PDF to the backend and display response."""
    if not token:
        history.append({"role": "assistant", "content": "⚠️ Please log in first!"})
        return None, history

    if pdf_file is None:
        history.append({"role": "assistant", "content": "⚠️ Please select a PDF file first."})
        return None, history

    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file, f, "application/pdf")}
            res = requests.post(f"{BASE_URL}/upload-pdf", files=files, headers=headers)

        if res.status_code == 200:
            msg = res.json().get("message", "✅ PDF uploaded successfully.")
            summary = res.json().get("summary", "")
            history.append({"role": "user", "content": f"📄 Uploaded: {pdf_file}"})
            history.append({"role": "assistant", "content": f"{msg}\n\n{summary}"})
        else:
            history.append({"role": "assistant", "content": f"❌ Upload failed: {res.text}"})
    except Exception as e:
        history.append({"role": "assistant", "content": f"❌ Exception during upload: {e}"})
    return None, history