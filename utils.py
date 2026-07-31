import json
from datetime import datetime, timedelta, timezone

import db
import auth


def get_client_ip(handler):
    """Respects X-Forwarded-For if present (useful if this ever sits behind
    a reverse proxy), otherwise falls back to the raw socket address."""
    forwarded = handler.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0]


def get_user_agent(handler):
    return handler.headers.get("User-Agent", "unknown")


def log_activity(user_id, action, ip_address, user_agent, metadata=None):
    db.execute(
        "INSERT INTO activity_logs (id, user_id, action, ip_address, user_agent, metadata, created_at) VALUES (?,?,?,?,?,?,?)",
        (auth.new_id(), user_id, action, ip_address, user_agent, json.dumps(metadata or {}), auth.now_iso()),
    )


def create_notification(user_id, title, message, notif_type="info", related_id=None):
    db.execute(
        "INSERT INTO notifications (id, user_id, title, message, type, related_id, is_read, created_at) VALUES (?,?,?,?,?,?,0,?)",
        (auth.new_id(), user_id, title, message, notif_type, related_id, auth.now_iso()),
    )


def rate_limited(bucket, identifier, max_hits, window_seconds):
    """Returns True if this identifier has hit the bucket too many times
    in the window (and should be blocked), otherwise records this attempt
    and returns False. Purely SQLite-backed, no external service needed."""
    conn = db.get_conn()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat()
    conn.execute("DELETE FROM rate_limit_hits WHERE bucket = ? AND created_at < ?", (bucket, cutoff))
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM rate_limit_hits WHERE bucket = ? AND identifier = ? AND created_at >= ?",
        (bucket, identifier, cutoff),
    ).fetchone()
    if row["c"] >= max_hits:
        conn.commit()
        return True
    conn.execute(
        "INSERT INTO rate_limit_hits (bucket, identifier, created_at) VALUES (?,?,?)",
        (bucket, identifier, auth.now_iso()),
    )
    conn.commit()
    return False


def valid_uid(uid: str) -> bool:
    return uid.isdigit() and 6 <= len(uid) <= 12


def valid_email(email: str) -> bool:
    # Deliberately simple per the spec ("basic format") — not a full RFC check.
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and " " not in email
