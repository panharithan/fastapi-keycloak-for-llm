## 🚀 Run Keycloak
### Create .env file and fill in credentials 
```
POSTGRES_USER=keycloak
POSTGRES_PASSWORD=<secret>
KC_DB_USERNAME=keycloak
KC_DB_PASSWORD=<secret>
KEYCLOAK_PORT=8080

KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=<secret>
```
⚠️ Replace <secret> with your real password or token.
Never commit your .env file to version control.


### Run Docker commands:
To start Keycloak
```
docker compose up -d
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

### 🔗 App URLs
KEYCLOAK_URL=http://localhost:8080
Keycloak Admin Console: http://localhost:8080/admin/master/console
KEYCLOAK_TOKEN_URL=http://localhost:8080/realms/llm/protocol/openid-connect/token
VERIFY_URL=http://localhost:8000/verify


## 🧩 Keycloak Configuration Guide

This project integrates **Keycloak** for authentication and authorization.  
Follow the steps below to configure Keycloak and set up environment variables for your Docker deployment.

---

### ⚙️ 1. Create a Realm

1. Open the Keycloak Admin Console at  
   👉 [http://localhost:8080/admin/master/console](http://localhost:8080/admin/master/console)
2. Log in using your **admin credentials**:

Username: llm_admin
Password: <secret>
3. Create a new **Realm**:
- Name: `llm`

---

### 👤 2. Create a Client

1. Inside your new **llm** realm, navigate to:

Clients → Create client

2. Configure the client as follows:
- **Client ID:** `chat-app`
- **Client Protocol:** `openid-connect`
- **Access Type:** `confidential`
- **Root URL:** `http://localhost:8000`
- **Valid Redirect URIs:** `http://localhost:8000/*`
- **Web Origins:** `*`
3. Save the client, then open its **Credentials** tab and copy the **Client Secret**.

---

### 👥 3. Create a User (for testing)

1. Go to `Users → Add user`
- **Username:** choose any username
- **Email:** your test email
- **First Name / Last Name:** optional
2. After creating, open the **Credentials** tab:
- Set a password (uncheck *Temporary* if you want it permanent).
- Enable “Email Verified” (optional for testing).
3. Click **Save**.

---

### ✉️ 4. Configure Email (optional, for verification links)

Go to:
Realm Settings → Email



Set:
- **Host:** `smtp.gmail.com`
- **Port:** `587`
- **From:** `<use-your-Google-mail>`
- **Username:** `<use-your-Google-mail>`
- **Password:** `<secret>`
- Enable TLS/STARTTLS

Click **Test Connection** to verify email works.

---
