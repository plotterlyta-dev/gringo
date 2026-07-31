import hashlib
import hmac
import secrets
import binascii
import os
from datetime import datetime, timedelta, timezone

import db

PBKDF2_ITERATIONS = 260_000
SESSION_LIFETIME_DAYS = 30

_SECRET_PATH = os.path.join(os.path.dirname(__file__), "data", "secret.key")


def get_server_secret():
    """Persisted so CSRF tokens survive a server restart during dev."""
    os.makedirs(os.path.dirname(_SECRET_PATH), exist_ok=True)
    if os.path.exists(_SECRET_PATH):
        with open(_SECRET_PATH, "r") as f:
            return f.read().strip()
    secret = secrets.token_hex(32)
    with open(_SECRET_PATH, "w") as f:
        f.write(secret)
    return secret


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str, salt: str = None):
    """PBKDF2-HMAC-SHA256 with a random salt, per the spec's preference."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return binascii.hexlify(dk).decode("utf-8"), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    # Constant-time compare to avoid leaking timing info about the hash.
    return secrets.compare_digest(candidate, stored_hash)


def create_session(user_id, ip_address, user_agent):
    session_id = secrets.token_urlsafe(32)
    created = now_iso()
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_LIFETIME_DAYS)).isoformat()
    db.execute(
        "INSERT INTO sessions (session_id, user_id, created_at, expires_at, ip_address, user_agent) VALUES (?,?,?,?,?,?)",
        (session_id, user_id, created, expires, ip_address, user_agent),
    )
    return session_id


def get_user_from_session(session_id):
    if not session_id:
        return None
    row = db.query_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    if not row:
        return None
    if row["expires_at"] < now_iso():
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        return None
    return db.query_one("SELECT * FROM users WHERE id = ?", (row["user_id"],))


def destroy_session(session_id):
    if session_id:
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def new_id():
    return secrets.token_hex(12)


def generate_referral_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous chars (0/O, 1/I)
    return "REF-" + "".join(secrets.choice(alphabet) for _ in range(6))


def csrf_token_for_session(session_id):
    """Derived from the session ID + server secret rather than stored
    separately — unpredictable to an attacker without the secret, and
    doesn't need its own DB column."""
    secret = get_server_secret()
    return hmac.new(secret.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_csrf(session_id, submitted_token):
    if not session_id or not submitted_token:
        return False
    expected = csrf_token_for_session(session_id)
    return secrets.compare_digest(expected, submitted_token)
