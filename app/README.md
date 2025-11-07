
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

##  🔐 Environment Configuration

Create a .env file to store sensitive parameters.
### Email Configuration

| Variable             | Description                                                                  |
|----------------------|------------------------------------------------------------------------------|
| EMAIL_HOST_USER       | Gmail address used to send verification emails.                             |
| EMAIL_HOST_PASSWORD   | Gmail App Password (not your main password!). Generate it from Google Account → Security → App Passwords. |

---

### Keycloak Admin Configuration

| Variable                | Description                                    |
|-------------------------|------------------------------------------------|
| KEYCLOAK_ADMIN_USERNAME | Keycloak admin account username used by the app. |
| KEYCLOAK_ADMIN_PASSWORD | Password for the Keycloak admin account.      |
| KEYCLOAK_REALM          | The Keycloak realm name.                        |

---

### Client App Configuration

| Variable      | Description                                 |
|---------------|---------------------------------------------|
| CLIENT_ID     | Keycloak client ID for user login (ROPG grant). |
| CLIENT_SECRET | Secret for the client ID.                    |


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
