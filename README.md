# fastapi-keycloak-for-llm
# ----------------------------
# Create .env file to store these params which contains sensitive info
# 🔐 Email Configuration
# ----------------------------
# Gmail address used to send verification emails.
EMAIL_HOST_USER=<GMail address>

# Gmail App Password (not your main password!)
# Generate it from Google Account → Security → App Passwords
EMAIL_HOST_PASSWORD=<secret>


# ----------------------------
# 🧱 Keycloak Admin Configuration
# ----------------------------
# Keycloak admin account used by the app to manage users.
KEYCLOAK_ADMIN_USERNAME=<admin username>
KEYCLOAK_ADMIN_PASSWORD=<secret>

# The Keycloak realm name
KEYCLOAK_REALM=<realm name>


# ----------------------------
# 💬 Client App Configuration
# ----------------------------
# Keycloak client credentials for user login (Resource Owner Password Grant)
CLIENT_ID=chat-app
CLIENT_SECRET=<secret>


# Note
"""
Email Token life time settins in keycloak:
->Override just the Email Verification
1. Go to "llm" realm or your realm name and choose "Realm Settings"
2. Scroll down to "Tokens" tab
3. Override Action Tokens
Find Email Verification
Enter your desired time (e.g. 1440 minutes = 24 hours)
4. Save changes
"""