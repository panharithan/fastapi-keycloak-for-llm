import pytest
from unittest.mock import patch, MagicMock
from jose.exceptions import JWTError
from app import keycloak_utils  # Adjust to your actual import path


# Dummy JWKS response
dummy_jwks = {
    "keys": [
        {"kid": "test-key-id", "kty": "RSA", "alg": "RS256", "use": "sig"}
    ]
}

dummy_token = "dummy.jwt.token"


def test_get_public_key_success():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = dummy_jwks
        keys = keycloak_utils.get_public_key()
        assert keys == dummy_jwks
        mock_get.assert_called_once_with(f"{keycloak_utils.ISSUER}/protocol/openid-connect/certs")


@patch("app.keycloak_utils.get_public_key", return_value=dummy_jwks)
@patch("app.keycloak_utils.jwt.get_unverified_header")
@patch("app.keycloak_utils.jwt.decode")
def test_verify_token_success(mock_decode, mock_unverified_header, mock_get_public_key):
    mock_unverified_header.return_value = {"kid": "test-key-id"}
    mock_decode.return_value = {"sub": "user123"}

    payload = keycloak_utils.verify_token(dummy_token)

    mock_get_public_key.assert_called_once()
    mock_unverified_header.assert_called_once_with(dummy_token)
    mock_decode.assert_called_once()
    assert payload == {"sub": "user123"}


@patch("app.keycloak_utils.get_public_key", return_value=dummy_jwks)
@patch("app.keycloak_utils.jwt.get_unverified_header")
def test_verify_token_missing_key(mock_unverified_header, mock_get_public_key):
    mock_unverified_header.return_value = {"kid": "nonexistent-key-id"}

    with pytest.raises(JWTError, match="Public key not found in JWKS"):
        keycloak_utils.verify_token(dummy_token)


@patch("app.keycloak_utils.get_public_key", return_value=dummy_jwks)
@patch("app.keycloak_utils.jwt.get_unverified_header")
@patch("app.keycloak_utils.jwt.decode")
def test_verify_token_decode_error(mock_decode, mock_unverified_header, mock_get_public_key):
    mock_unverified_header.return_value = {"kid": "test-key-id"}
    mock_decode.side_effect = JWTError("Signature verification failed")

    with pytest.raises(JWTError, match="Invalid token: Signature verification failed"):
        keycloak_utils.verify_token(dummy_token)