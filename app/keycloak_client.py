import requests
import base64
import json
from settings import KEYCLOAK_URL, REALM, KEYCLOAK_TOKEN_URL, CLIENT_ID, CLIENT_SECRET


def decode_jwt(token: str):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        # Add padding if necessary for base64 decoding
        padding = '=' * (4 - len(payload) % 4)
        payload += padding
        decoded_bytes = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_bytes)
    except Exception as e:
        print(f"Failed to decode JWT: {e}")
        return None

def keycloak_login(username: str, password: str):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    resp = requests.post(KEYCLOAK_TOKEN_URL, data=data)
    if resp.status_code != 200:
        error = resp.json().get("error_description", "Login failed")
        return None, error

    access_token = resp.json().get("access_token")

    # Try fetching userinfo
    userinfo_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_resp = requests.get(userinfo_url, headers=headers)

    if userinfo_resp.status_code == 200:
        userinfo = userinfo_resp.json()
        if not userinfo.get("email_verified", False):
            return None, "Email is not verified"
        return access_token, None
    else:
        print(f"Userinfo error status: {userinfo_resp.status_code}")
        print(f"Userinfo error response: {userinfo_resp.text}")
        # Fallback: decode access token directly
        claims = decode_jwt(access_token)
        if not claims:
            return None, "Failed to decode access token"
        if not claims.get("email_verified", False):
            return None, "Email is not verified"
        return access_token, None
