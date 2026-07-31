CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  referral_code TEXT UNIQUE NOT NULL,
  referred_by_user_id TEXT REFERENCES users(id),
  coins_balance INTEGER NOT NULL DEFAULT 0,
  coins_on_hold INTEGER NOT NULL DEFAULT 0,
  last_spin_at TEXT,
  created_at TEXT NOT NULL,
  last_login_at TEXT,
  last_login_ip TEXT,
  last_login_user_agent TEXT,
  is_admin INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  can_refer INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS topups (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  coins INTEGER NOT NULL,
  amount_naira INTEGER NOT NULL,
  payment_method TEXT NOT NULL DEFAULT 'manual',
  reference TEXT UNIQUE NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS redemption_requests (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  uid_submitted TEXT NOT NULL,
  coins_requested INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending_approval',
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  resolved_by_admin_id TEXT,
  admin_note TEXT
);

CREATE TABLE IF NOT EXISTS referrals (
  id TEXT PRIMARY KEY,
  referrer_id TEXT NOT NULL REFERENCES users(id),
  referred_id TEXT UNIQUE NOT NULL REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'pending',
  bonus_coins_awarded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS spin_logs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  prize_coins INTEGER NOT NULL,
  is_jackpot INTEGER NOT NULL DEFAULT 0,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_logs (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  action TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  metadata TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'info',
  related_id TEXT,
  is_read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id, created_at);

-- Simple in-DB rate limiting: one row per (bucket, ip) attempt.
CREATE TABLE IF NOT EXISTS rate_limit_hits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bucket TEXT NOT NULL,
  identifier TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_lookup ON rate_limit_hits (bucket, identifier, created_at);
