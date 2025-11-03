import os
import requests

# =========================
# 🔧 CONFIGURATION CONSTANTS
# =========================

# You can override these via environment variables for flexibility
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Derived URLs
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_VERSION_URL = f"{OLLAMA_BASE_URL}/api/version"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

# Sanity test prompt
TEST_PROMPT = "Hello, sanity check!"

# =========================
# 🚦 SANITY CHECK FUNCTION
# =========================

def sanity_check():
    """Verify Ollama API connectivity and generation functionality."""
    try:
        # 1️⃣ Check version endpoint
        health_resp = requests.get(OLLAMA_VERSION_URL, timeout=5)
        if health_resp.status_code != 200:
            print(f"❌ Ollama server reachable but returned status {health_resp.status_code}")
            return False

        version = health_resp.json().get("version", "unknown")
        print(f"✅ Ollama server reachable: version = {version}")

        # 2️⃣ Test generation endpoint
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": TEST_PROMPT,
            "stream": False,
        }
        gen_resp = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=10)
        if gen_resp.status_code != 200:
            print(f"❌ API /generate endpoint returned {gen_resp.status_code}")
            return False

        data = gen_resp.json()
        response_text = data.get("response", "")
        if response_text:
            print(f"✅ LLM responded: {response_text[:60]}...")
            return True
        else:
            print("❌ LLM responded but no text returned.")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Ollama API: {e}")
        return False


# =========================
# 🚀 MAIN
# =========================

if __name__ == "__main__":
    if sanity_check():
        print("🎯 Sanity check passed! Ollama API is working.")
    else:
        print("⚠️ Sanity check failed! Check your Ollama server.")