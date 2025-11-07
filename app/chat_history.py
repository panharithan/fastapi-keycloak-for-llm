# chat_history.py
import pytz
from pymongo import MongoClient
from datetime import datetime
from .settings import TIMEZONE, DATE_TIME_FORMATE
from .db import chats


def format_message(role, content, timestamp=None):
    """Return formatted chat message with TIMEZONE timestamp"""
    if timestamp:
        # Parse ISO8601 timestamp from backend
        dt = datetime.fromisoformat(timestamp)
        dt = dt.replace(tzinfo=pytz.UTC).astimezone(TIMEZONE)
    else:
        dt = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(TIMEZONE)
    formatted_ts = dt.strftime(DATE_TIME_FORMATE)
    formatted_content = f"{content}\n\n<span style='font-size:0.8em; color:gray;'>🕒 {formatted_ts}</span>"
    return {"role": role, "content": formatted_content}

def save_user_message(username, role, content):
    chats.insert_one({
        "username": username,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })

def get_user_history(username):
    messages = chats.find({"username": username}).sort("timestamp", 1)
    return [
        {
            # ✅ Safe get() for backward compatibility
            "role": msg.get("role", "user"),
            "content": msg.get("content") or msg.get("message", ""),
            "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat(),
        }
        for msg in messages
    ]

def clear_history(username):
    chats.delete_many({"username": username})
