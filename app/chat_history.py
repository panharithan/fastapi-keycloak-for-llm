import pytz
from datetime import datetime
from .settings import TIMEZONE, DATE_TIME_FORMAT, fernet
from .db import chats


def encrypt_message(text: str) -> str:
    """Encrypt message content before saving to MongoDB"""
    return fernet.encrypt(text.encode()).decode()


def decrypt_message(token: str) -> str:
    """Decrypt message content when reading from MongoDB"""
    try:
        return fernet.decrypt(token.encode()).decode()
    except Exception:
        # Handle backward compatibility with unencrypted records
        return token


def format_message(role, content, timestamp=None):
    """Return formatted chat message with TIMEZONE-aware timestamp"""
    if timestamp:
        # Parse ISO8601 timestamp from backend or MongoDB
        dt = datetime.fromisoformat(timestamp)
        dt = dt.replace(tzinfo=pytz.UTC).astimezone(TIMEZONE)
    else:
        dt = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(TIMEZONE)

    formatted_ts = dt.strftime(DATE_TIME_FORMAT)
    formatted_content = (
        f"{content}\n\n"
        f"<span style='font-size:0.8em; color:gray;'>🕒 {formatted_ts}</span>"
    )
    return {"role": role, "content": formatted_content}


def save_user_message(username: str, role: str, content: str):
    """Encrypt and store chat message in MongoDB"""
    encrypted_content = encrypt_message(content)
    chats.insert_one({
        "username": username,
        "role": role,
        "content": encrypted_content,
        "timestamp": datetime.utcnow(),
    })


def get_user_history(username):
    messages = chats.find({"username": username}).sort("timestamp", 1)
    results = []

    for msg in messages:
        content = msg.get("content") or msg.get("message", "")
        # Try decrypting, but fall back to plaintext for legacy docs
        try:
            content = decrypt_message(content)
        except Exception:
            pass  # legacy message, not encrypted

        results.append({
            "role": msg.get("role", "user"),
            "content": content,
            "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat(),
        })

    return results


def clear_history(username: str):
    """Delete all chat messages for a given user"""
    chats.delete_many({"username": username})
