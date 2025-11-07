# app/tests/test_chat_history_module.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytz

from app.chat_history import (
    format_message,
    save_user_message,
    get_user_history,
    clear_history,
)


# -------------------------------
# Constants for testing
# -------------------------------
@pytest.fixture
def mock_chats():
    """Mock MongoDB collection"""
    with patch("app.chat_history.chats", autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_time(monkeypatch):
    """Freeze time to a known UTC value"""
    fixed_now = datetime(2025, 11, 7, 12, 0, 0, tzinfo=pytz.UTC)
    monkeypatch.setattr("app.chat_history.datetime", MagicMock())
    app_dt = __import__("app.chat_history").chat_history.datetime
    app_dt.utcnow.return_value = fixed_now.replace(tzinfo=None)
    app_dt.fromisoformat.side_effect = datetime.fromisoformat
    app_dt.strptime = datetime.strptime
    app_dt.strftime = datetime.strftime
    app_dt.replace = datetime.replace
    return fixed_now


# -------------------------------
# Tests for format_message()
# -------------------------------
def test_format_message_without_timestamp(mock_time):
    msg = format_message("user", "Hello world!")
    assert msg["role"] == "user"
    assert "Hello world!" in msg["content"]
    assert "🕒" in msg["content"]
    assert "2025" in msg["content"]  # contains year
    assert "gray" in msg["content"]  # formatted span


def test_format_message_with_timestamp(mock_time):
    ts = datetime(2025, 11, 7, 9, 30, 0).isoformat()
    msg = format_message("assistant", "Hi there!", timestamp=ts)

    assert msg["role"] == "assistant"
    assert "Hi there!" in msg["content"]
    # Ensure timestamp span and date info exist
    assert "🕒" in msg["content"]
    assert any(part in msg["content"] for part in ["2025", "Nov", "11", "07"])

# -------------------------------
# Tests for save_user_message()
# -------------------------------
def test_save_user_message_inserts(mock_chats, mock_time):
    save_user_message("test_user", "user", "Hello again!")
    mock_chats.insert_one.assert_called_once()
    args, kwargs = mock_chats.insert_one.call_args
    doc = args[0]
    assert doc["username"] == "test_user"
    assert doc["role"] == "user"
    assert "timestamp" in doc


# -------------------------------
# Tests for get_user_history()
# -------------------------------
def test_get_user_history_returns_sorted(mock_chats, mock_time):
    # Mock MongoDB find() → sort() chain
    mock_chats.find.return_value.sort.return_value = [
        {"role": "user", "content": "Hi", "timestamp": datetime(2025, 11, 7, 10, 0, 0)},
        {"role": "assistant", "content": "Hello", "timestamp": datetime(2025, 11, 7, 10, 1, 0)},
    ]
    history = get_user_history("test_user")

    mock_chats.find.assert_called_once_with({"username": "test_user"})
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert "timestamp" in history[0]
    assert isinstance(history[0]["timestamp"], str)


def test_get_user_history_backward_compatibility(mock_chats, mock_time):
    """Ensure old Mongo documents with 'message' instead of 'content' still work"""
    mock_chats.find.return_value.sort.return_value = [
        {"role": "assistant", "message": "Legacy format", "timestamp": datetime(2025, 11, 7, 8, 0, 0)},
    ]
    history = get_user_history("legacy_user")
    assert len(history) == 1
    assert history[0]["content"] == "Legacy format"


# -------------------------------
# Tests for clear_history()
# -------------------------------
def test_clear_history_deletes(mock_chats):
    clear_history("test_user")
    mock_chats.delete_many.assert_called_once_with({"username": "test_user"})
