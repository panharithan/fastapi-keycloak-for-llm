
# Development Env Set Up
---
Note: Check tools versions in READMD.md in root folder

## Build Ollama 
Download and install Ollama from its webpage https://ollama.com/download


Pull the model (e.g., llama3.2)
```
ollama pull llama3.2
```

Run the model with your prompt
```
ollama run llama3.2 "Hello!"
```

Check available models
```
ollama list
NAME               ID              SIZE      MODIFIED   
llama3.2:latest    a80c4f17acd5    2.0 GB    7 days ago    
```

## 🖥️ Add Keycloak Hostname to Your PC (If Hosting Locally)

Edit your hosts file to map `keycloak` to `localhost`:

```bash
sudo nano /etc/hosts
```
Add the following line (change IP address if Keycloak is hosted seperately):
```
127.0.0.1    keycloak
```

For Keycloak configurations, check file keycloak/README.md

⸻

## Key Generation for chat history encryption on MongoDB
```
pip install cryptography
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

acQ9sqn8nwdydAFA9CStb6UMwn0174-v1Ou3P1umXnk=
```
Use this key for `ENCRYPTION_KEY` variable in .env file below

##  🔐 Environment Configuration

Create a .env file to store sensitive parameters.
### LLM Configuration

| Variable          | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| OLLAMA_API_URL    | The local API endpoint for Ollama used by the app to generate responses. Set to `http://host.docker.internal:11434/api/generate` to allow Docker containers to access the host’s Ollama instance. |
| AVAILABLE_MODELS             | The models name used by Ollama for text generation, e.g., `llama3.2,gemma3,phi3` |



### Email Configuration

| Variable             | Description                                                                  |
|----------------------|------------------------------------------------------------------------------|
| EMAIL_HOST_USER       | Gmail address used to send verification emails.                             |
| EMAIL_HOST_PASSWORD   | Gmail App Password (not your main password!). Generate it from Google Account → Security → App Passwords. |
| EMAIL_HOST            | SMTP server hostname (e.g., smtp.gmail.com).                                |
| EMAIL_PORT            | SMTP server port (e.g., 587).                                               |
| EMAIL_USE_TLS         | Enable TLS for SMTP (true/false).                                           |

---

### Keycloak Admin Configuration

| Variable                | Description                                    |
|-------------------------|------------------------------------------------|
| KEYCLOAK_ADMIN_USERNAME | Keycloak admin account username used by the app. |
| KEYCLOAK_ADMIN_PASSWORD | Password for the Keycloak admin account.      |
| KEYCLOAK_REALM          | The Keycloak realm name.                        |
| KEYCLOAK_HOST           | Hostname or service name of the Keycloak server (e.g., keycloak).           |
| KEYCLOAK_PORT           | The Keycloak port number (default 8080).      |

---

### Client App Configuration

| Variable      | Description                                 |
|---------------|---------------------------------------------|
| CLIENT_ID     | Keycloak client ID for user login (ROPG grant). |
| CLIENT_SECRET | Secret for the client ID.                    |
| BASE_URL      | Base URL of your backend API (e.g., http://localhost:8000). Used by the UI to make API requests.|

---

### MongoDB Configuration

| Variable      | Description                                     |
|---------------|------------------------------------------------|
| MONGO_USER    | MongoDB username for database authentication.  |
| MONGO_PASS    | MongoDB password for database authentication.  |
| MONGO_HOST    | MongoDB host address (e.g., localhost, mongodb).|
| MONGO_DB_PORT | Port on which MongoDB is running (default 27017).|
| MONGO_DB      | Name of the MongoDB database to use.             |
| ENCRYPTION_KEY | Encryption key for chat history collection            |

---

### Environment variables for FastAPI Base URLs

| Variable         | Description                                                                                           |
|------------------|-----------------------------------------------------------------------------------------------------|
| BASE_URL         | Base URL for non-production Docker Compose usage, e.g., `http://localhost:8000`. Used internally by backend and UI for API requests.|
| PUBLIC_BASE_URL   | Public-facing base URL for production, used in email links and browser, e.g., `http://llm.local`.    |
| VERIFY_URL       | Verification URL used in production for email tokens, e.g., `http://app:8000/verify?token=`. Used internally in Docker for backend calls.|

---

### Example values

**For non-production Docker Compose:**

```env
BASE_URL=http://localhost:8000
PUBLIC_BASE_URL=http://localhost:8000
```

Full example of .env for non-production Docker compose file
```
# SMTP
EMAIL_HOST_USER=an.*****@gmail.com
EMAIL_HOST_PASSWORD=**************
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Keycloak
KEYCLOAK_ADMIN_USERNAME=llm_admin
KEYCLOAK_ADMIN_PASSWORD=********
KEYCLOAK_REALM=llm
KEYCLOAK_PORT=8080
KEYCLOAK_HOST=keycloak

CLIENT_ID=chat-app
CLIENT_SECRET=***********************

# MongoDB
MONGO_USER=admin
MONGO_PASS=********
MONGO_HOST=localhost
MONGO_DB_PORT=27017
MONGO_DB=chat_app_db
ENCRYPTION_KEY=acQ9sqn8nwdydAFA9CStb6UMwn0174-v1Ou3P1umXnk= # change this

# URLs
BASE_URL=http://localhost:8000
PUBLIC_BASE_URL=http://localhost:8000 # for local dev & non-production Docker env

# LLM / Ollama
OLLAMA_API_URL=http://localhost:11434/api/generate
AVAILABLE_MODELS=llama3.2,gemma3,phi3

# Optional Timezone and Format (defaults set in settings.py)
TIMEZONE=Europe/Berlin
DATE_TIME_FORMAT=%d-%m-%Y %H:%M:%S
```

##  🚀 Run Development Commands
1. Install Python dependencies (using Python virtual environment is highly recommended) from root folder.

E.g in Linux or MacOS
```
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

Install Python dependencies
```
pip install -r requirements.txt

```
2.	Start FastAPI app (run from the root folder of the project):

```
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

Access API at: http://localhost:8000/

Access API docs at: http://localhost:8000/docs

Or use the postman.json file for Postman (import the json file)

3.	Start Gradio UI (run from the root folder of the project):

```
python -m app.ui
```

Access UI at: http://localhost:7860/

4.	Run unit tests (from the root folder):
	
```
pytest --cov=app --cov-report=term-missing -v
```
save report
```
pytest --cov=app --cov-report=term-missing -v > app/tests/pytest_report.txt
```
⸻

## ⚙️ Notes

### Email Token Lifetime Settings in Keycloak
```
To override Email Verification token lifetime:
	1.	Go to your realm (e.g. llm) in Keycloak Admin Console.
	2.	Navigate to Realm Settings → Tokens tab.
	3.	Under Override Action Tokens, find Email Verification.
	4.	Enter desired time in minutes (e.g., 1440 for 24 hours).
	5.	Save changes.
```
⸻

###  Configure Keycloak’s Bruteforce Protection
```
	1.	Login to the Keycloak Admin Console.
	2.	Go to your realm (e.g., llm).
	3.	Navigate to:
Realm Settings → Security Defenses → Brute Force Detection
	4.	Enable it by turning Enabled ON.
	5.	Configure options like Lockout Temporarily, Max Login Failures, etc. (Refer to Keycloak docs for detailed options).
```
