import pytest
from unittest.mock import patch, MagicMock
import app.llm  # Adjust the import path if needed
from app.settings import MODEL
# Patch requests.post and also patch MODEL and OLLAMA_API_URL constants inside the llm module

@patch("app.llm.requests.post")
@patch("app.llm.MODEL", MODEL)
@patch("app.llm.OLLAMA_API_URL", "http://localhost:11434")
def test_get_response_success(mock_post):
    # Setup mock response JSON
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Hello, world!"}
    mock_post.return_value = mock_response

    prompt = "Say hello"
    result = app.llm.get_response(prompt)

    # Validate the call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://localhost:11434"
    assert kwargs["json"]["prompt"] == prompt
    assert kwargs["json"]["model"] == MODEL
    assert kwargs["json"]["stream"] is False

    # Validate function return
    assert result == "Hello, world!"


@patch("app.llm.requests.post")
@patch("app.llm.MODEL", MODEL)
@patch("app.llm.OLLAMA_API_URL", "http://localhost:11434")
def test_get_response_no_response_key(mock_post):
    # Mock response without "response" key
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    prompt = "Empty response test"
    result = app.llm.get_response(prompt)

    assert result == ""


@patch("app.llm.requests.post")
@patch("app.llm.MODEL", MODEL)
@patch("app.llm.OLLAMA_API_URL", "http://localhost:11434")
def test_get_response_raises_exception(mock_post):
    # Simulate a requests exception
    mock_post.side_effect = Exception("Network error")

    prompt = "Test exception"

    with pytest.raises(Exception) as excinfo:
        app.llm.get_response(prompt)
    
    assert "Network error" in str(excinfo.value)