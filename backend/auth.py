"""Minimal dependency-light authentication helpers (PBKDF2 + HS256 JWT)."""
import base64, hashlib, hmac, json, os, secrets, time
from fastapi import HTTPException, Request
from config import settings

# Read the same validated setting used by the rest of the backend.
SECRET_KEY = settings.jwt_secret_key


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return f"pbkdf2_sha256$310000${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt_s, digest_s = stored.split("$")
        if scheme != "pbkdf2_sha256": return False
        salt = base64.urlsafe_b64decode(salt_s + "=" * (-len(salt_s) % 4))
        expected = base64.urlsafe_b64decode(digest_s + "=" * (-len(digest_s) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, email: str) -> str:
    secret = settings.jwt_secret_key
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 characters")
    now = int(time.time())
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub":str(user_id),"email":email,"iat":now,"exp":now + 60*60*24*7}, separators=(",", ":")).encode())
    signing = f"{header}.{payload}"
    signature = _b64(hmac.new(secret.encode(), signing.encode(), hashlib.sha256).digest())
    return f"{signing}.{signature}"


def decode_access_token(token: str) -> dict:
    secret = settings.jwt_secret_key
    if len(secret) < 32: raise HTTPException(status_code=503, detail="Authentication is not configured")
    try:
        header, payload, signature = token.split(".")
        signing = f"{header}.{payload}"
        expected = _b64(hmac.new(secret.encode(), signing.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError("signature")
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data.get("exp", 0)) < int(time.time()): raise ValueError("expired")
        int(data["sub"])
        return data
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")


def get_user_id_from_request(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please sign in to continue")
    return int(decode_access_token(auth[7:])["sub"])
