import requests
from .settings import OLLAMA_API_URL, MODEL


def get_response(prompt: str, model: str = MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # stream=True if you want streaming responses
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    print("calling LLM: response = ", response)
    data = response.json()
    return data.get("response", "")
