# db.py
from pymongo import MongoClient
import os

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_HOST = os.getenv("MONGO_HOST")  # Docker service name
MONGO_DB   = os.getenv("MONGO_DB")
MONGO_DB_PORT = os.getenv("MONGO_DB_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:27017/{MONGO_DB}?authSource=admin"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
chats = db["chat_history"]