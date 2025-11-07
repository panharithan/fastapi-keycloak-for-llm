
## Run MongoDB

### Create `.env` file and fill in credentials
```
MONGO_USER=admin
MONGO_PASS=<secret>
MONGO_HOST=localhost
MONGO_DB_PORT=27017
MONGO_DB=chat_app_db
```
⚠️ Replace credentials with secure values in production.  
Never commit your `.env` file to version control.

---
### Run Docker commands:

To start MongoDB
```
docker compose up -d mongo
```

To stop MongoDB
```
docker compose down -v
```

To restart MongoDB
```
docker compose down -v
docker compose up -d mongo
```

### 🔗 MongoDB Access Info
MongoDB URI
```
mongodb://admin:admin@localhost:27017/chat_app_db
```
Access via MongoDB clients such as MongoDB Compass￼ or mongo shell CLI.

### 🧩 MongoDB Usage Notes
•	The database chat_app_db is used to persist chat history for the app.

•	Ensure your backend service connects using the environment variables for username, password, host, and port.

•	In production, secure your MongoDB with strong credentials and restrict network access.
