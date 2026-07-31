import sqlite3
import os
import threading

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "store.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

_local = threading.local()


def get_conn():
    """One SQLite connection per thread (http.server handles each request
    on the ThreadingHTTPServer's own thread), with foreign keys enforced
    and row access by column name."""
    if not hasattr(_local, "conn"):
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # lets reads/writes overlap safely
        _local.conn = conn
    return _local.conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_conn()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    _migrate(conn)


def _migrate(conn):
    """Adds columns introduced after the initial schema, without wiping
    an existing store.db. Safe to run every startup — each ALTER is
    skipped if the column already exists."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "can_refer" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN can_refer INTEGER NOT NULL DEFAULT 1")
        conn.commit()

    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "notifications" not in tables:
        conn.execute("""
            CREATE TABLE notifications (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL REFERENCES users(id),
              title TEXT NOT NULL,
              message TEXT NOT NULL,
              type TEXT NOT NULL DEFAULT 'info',
              related_id TEXT,
              is_read INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX idx_notifications_user ON notifications (user_id, created_at)")
        conn.commit()


def query(sql, params=()):
    conn = get_conn()
    cur = conn.execute(sql, params)
    return cur.fetchall()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Single statement, auto-commits. For multi-statement atomic
    operations (wallet holds/approvals), use transaction() instead."""
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur


class transaction:
    """Context manager wrapping a set of statements in one atomic commit,
    rolling back automatically if anything inside raises."""

    def __enter__(self):
        self.conn = get_conn()
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False
