from fastapi.testclient import TestClient
from unittest.mock import patch
from app.app import app, get_current_user  # Import FastAPI instance here

client = TestClient(app)

def fake_get_current_user():
    return {"preferred_username": "testuser"}

def test_generate_text():
    app.dependency_overrides[get_current_user] = fake_get_current_user

    with patch("app.app.get_response", return_value="Hello world!"):
        payload = {"text": "Hi"}
        headers = {"Authorization": "Bearer faketoken"}
        response = client.post("/generate", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["response"] == "Hello world!"

    app.dependency_overrides.clear()