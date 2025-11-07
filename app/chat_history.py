# chat_history.py
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://admin:admin@localhost:27017/chat_app_db?authSource=admin")
db = client["chat_app_db"]
collection = db["chat_history"]

def save_user_message(username, role, content):
    collection.insert_one({
        "username": username,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })

def get_user_history(username):
    messages = collection.find({"username": username}).sort("timestamp", 1)
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
    collection.delete_many({"username": username})
