
## 🚀 Deployment with Docker Compose (Non-Production Environment)
### Project Overview
This open-source project is a large language model (LLM) chat application powered by Ollama. You can run your favorite Ollama model with a friendly chat interface or deploy it for team or organizational use, enabling a private, secure, and customizable AI assistant environment within your infrastructure. All's license free.

It features a Gradio Web UI for user interaction and a FastAPI backend that handles chat requests, model responses, and system orchestration. The backend is secured with Keycloak OAuth2, ensuring authenticated access and role-based authorization for users. Chat history is stored in MongoDB for fast, scalable storage, and encrypted by secure Fernet symmetric encryption.

Video Demo on Youtube https://youtu.be/hYHatP0JVQ8

### Diagram of Architecture
![System Architecture Diagram](drawing/diagram.png)

---

### Tool Versions Used in This Project's Development  
*(Updated: November 2025 — verified latest stable releases)*  

| Tool | Version |
|------|----------|
| **Python** | 3.12.6 |
| **pip** | 25.3 |
| **pytest** | 8.4.2 |
| **Dependencies** | requirements.txt |
| **Ollama CLI** | 0.3.14 |
| **Docker** | 27.3.1 |
| **Docker Compose** | 2.29.2 |
| **Keycloak (Docker image)** | `quay.io/keycloak/keycloak:26.4` |
| **PostgreSQL (Docker image)** | `postgres:18.0` |
| **MongoDB (Docker image)** | `mongo:8.2.1-noble` |

---

✅ *All tools and images above reflect stable or long-term supported (LTS) versions as of November 2025.*

### 🧩 Step 1 — Build 
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

### 🧩 Step 2— Create a Docker Network (from root folder)
```bash
docker network create llm-net
```
### 🔑 Step 3 — Bring Keycloak Up (in keycloak folder)
Check keycloak/README.md
Connect to llm-net Docker network
```
docker network connect llm-net keycloak 
```
### 🗄️ Step 4 — Bring MongoDB Up (in mongodb folder)
Check mongodb/README.md
```
docker network connect llm-net mongodb 
```

### ⚙️ Step 5 — Bring the FastAPI + Gradio App Up (from root folder)
Key Generation for chat history encryption on MongoDB
```
pip install cryptography
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

acQ9sqn8nwdydAFA9CStb6UMwn0174-v1Ou3P1umXnk=
```
Use this key for `ENCRYPTION_KEY` variable in .env file below


Create a .env file to store sensitive parameters.
### LLM Configuration

| Variable          | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| OLLAMA_API_URL    | The local API endpoint for Ollama used by the app to generate responses. Set to `http://host.docker.internal:11434/api/generate` to allow Docker containers to access the host’s Ollama instance. |
| AVAILABLE_MODELS             | The models name used by Ollama for text generation, e.g., `["llama3.2", "gemma3"]` |


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

For production Docker Compose:
```
# Internal calls inside Docker (backend self-calls)
BASE_URL=http://app:8000
VERIFY_URL=http://app:8000/verify?token=

# Public-facing links (emails, browser)
PUBLIC_BASE_URL=http://llm.local
```

Full example of .env for non-production Docker compose file
```
# for docker variables and deployment. Variable names are the same to app/.env (development)
OLLAMA_API_URL = "http://host.docker.internal:11434/api/generate"
AVAILABLE_MODELS=["llama3.2", "gemma3"]

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

EMAIL_HOST_USER=an.*****@gmail.com
EMAIL_HOST_PASSWORD=**************

KEYCLOAK_HOST=keycloak
KEYCLOAK_ADMIN_USERNAME=llm_admin
KEYCLOAK_ADMIN_PASSWORD=********
KEYCLOAK_REALM=llm
KEYCLOAK_PORT=8080
CLIENT_ID=chat-app
CLIENT_SECRET=***********************

MONGO_USER=admin
MONGO_PASS=********
MONGO_HOST=mongodb
MONGO_DB_PORT=27017
MONGO_DB=chat_app_db
ENCRYPTION_KEY=acQ9sqn8nwdydAFA9CStb6UMwn0174-v1Ou3P1umXnk= # change this

# FastAPI
BASE_URL=http://localhost:8000
PUBLIC_BASE_URL=http://localhost:8000
```

Full .env file for production Docker Compose with Nginx as reverse proxy. Assuming http://llm.local is the domain name
```
# for docker variables and deployment. Variable names are the same to app/.env (development)
OLLAMA_API_URL = "http://host.docker.internal:11434/api/generate"
AVAILABLE_MODELS=["llama3.2", "gemma3"]

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

EMAIL_HOST_USER=an.*****@gmail.com
EMAIL_HOST_PASSWORD=**************

KEYCLOAK_HOST=keycloak
KEYCLOAK_ADMIN_USERNAME=llm_admin
KEYCLOAK_ADMIN_PASSWORD=********
KEYCLOAK_REALM=llm
KEYCLOAK_PORT=8080
CLIENT_ID=chat-app
CLIENT_SECRET=***********************

MONGO_USER=admin
MONGO_PASS=********
MONGO_HOST=mongodb
MONGO_DB_PORT=27017
MONGO_DB=chat_app_db
ENCRYPTION_KEY=acQ9sqn8nwdydAFA9CStb6UMwn0174-v1Ou3P1umXnk= # change this

# Internal calls inside Docker
BASE_URL=http://app:8000
VERIFY_URL=http://app:8000/verify?token=

# Public-facing links (emails, browser)
PUBLIC_BASE_URL=http://llm.local
```

Run Docker commands
```
docker compose up -d
```
Or, if you want to rebuild with environment variables:
```
docker-compose --env-file .env up --build
```


To stop
```
docker down -v
```

To restart
```
docker down -v
docker compose up -d
```

For production environment, consider using Nginx (configuration check `nginx` folder) and follow `docker-compose.prod.yml` file. Sample command:
```
docker compose -f docker-compose.prod.yml up --build -d
```

⸻

### 🌐 Access the Services
```
Service	URL
FastAPI API	http://localhost:8000
API	Docs	http://localhost:8000/docs	
(or check app/postman.json file)￼
Gradio UI	http://localhost:7860￼
Keycloak	http://localhost:8080
MongoDB 	mongodb://localhost:27017 
(access via MongoDB client or tools like MongoDB Compass)
```

Or for Production environment. Assuming http://llm-local is the domain name
```
Service	URL
Web Server	http://llm-local
Keycloak	http://localhost:8080
MongoDB 	mongodb://localhost:27017
(Keycloak and MongoDB are deployed seperatedly and not managed by Nginx reverse proxy.)
```

### Troubleshooting

If you are unable to log in, it might be due to connection issues with Keycloak. Make sure your containers are connected to the correct Docker network. You can connect Keycloak to the `llm-net` network with:

```
docker network connect llm-net keycloak
```

Similarly, if you experience connection issues with MongoDB, ensure the MongoDB container is also connected to the llm-net network:
```
docker network connect llm-net keycloak 
```

### Video Demo on Youtube
 https://youtu.be/hYHatP0JVQ8
