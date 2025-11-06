# keycloak_utils.py
from jose import jwt
from jose.exceptions import JWTError
import requests
from .settings import ISSUER, ENCRYPTION_ALGO, AUDIENCE

def get_public_key():
    res = requests.get(f"{ISSUER}/protocol/openid-connect/certs")
    return res.json()

def verify_token(token: str):
    jwks = get_public_key()
    unverified_header = jwt.get_unverified_header(token)
    key = next(
        (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]),
        None
    )
    if not key:
        raise JWTError("Public key not found in JWKS")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[ENCRYPTION_ALGO],
            audience=AUDIENCE,
            issuer=ISSUER
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}")
