import json
import os
import re
import mimetypes
import random
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

import env
env.load_dotenv()

import db
import auth
import utils
import layout
import views
import payment

PORT = int(os.environ.get("PORT", 8000))
DEV_MODE = os.environ.get("DEV_MODE", "1") == "1"
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", f"http://127.0.0.1:{PORT}").rstrip("/")
NAIRA_PER_COIN = 5
REFERRAL_BONUS_COINS = 50
SPIN_COOLDOWN_HOURS = 24

# Segment order MUST match the wheel drawn in views.spin_page's JS so the
# slice index returned by /api/spin lands the animation on the true result.
SPIN_SEGMENTS = [
    {"coins": 1, "weight": 22},
    {"coins": 2, "weight": 18},
    {"coins": 3, "weight": 15},
    {"coins": 5, "weight": 13},
    {"coins": 6, "weight": 11},
    {"coins": 7, "weight": 9},
    {"coins": 8, "weight": 6},
    {"coins": 10, "weight": 4},
    {"coins": 15, "weight": 1.9},
    {"coins": 50, "weight": 0.1, "jackpot": True},
]

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")

ADMIN_REDEMPTION_RE = re.compile(r"^/admin/redemptions/([a-f0-9]+)/(approve|reject)$")
ADMIN_USER_ACTION_RE = re.compile(r"^/admin/users/([a-f0-9]+)/(ban|unban|restrict-referral|allow-referral)$")
ADMIN_USER_DETAIL_RE = re.compile(r"^/admin/users/([a-f0-9]+)$")



def pick_weighted_segment():
    total = sum(s["weight"] for s in SPIN_SEGMENTS)
    r = random.SystemRandom().uniform(0, total)  # secrets-grade randomness (SystemRandom uses os.urandom)
    upto = 0
    for i, seg in enumerate(SPIN_SEGMENTS):
        upto += seg["weight"]
        if r <= upto:
            return i, seg
    return len(SPIN_SEGMENTS) - 1, SPIN_SEGMENTS[-1]


def credit_topup(reference, source="manual_topup"):
    """Marks a pending topup as success and credits the wallet, fires a
    notification, and checks for a first-purchase referral bonus. Called
    from the dev simulator, the Paystack redirect callback, AND the
    Paystack webhook — so it's written to be idempotent: if the topup is
    already 'success' (e.g. both the callback and webhook fired for the
    same payment), it's a safe no-op rather than double-crediting."""
    topup = db.query_one("SELECT * FROM topups WHERE reference = ?", (reference,))
    if not topup or topup["status"] == "success":
        return

    with db.transaction() as conn:
        conn.execute("UPDATE topups SET status = 'success' WHERE id = ?", (topup["id"],))
        conn.execute("UPDATE users SET coins_balance = coins_balance + ? WHERE id = ?", (topup["coins"], topup["user_id"]))

    utils.log_activity(topup["user_id"], source, topup["ip_address"] or "unknown", topup["user_agent"] or "unknown",
                        {"coins": topup["coins"], "reference": reference})
    utils.create_notification(
        topup["user_id"],
        "Coins added! 🎉",
        f"{topup['coins']} coins (₦{topup['amount_naira']:,}) have been added to your wallet.",
        notif_type="topup_success",
        related_id=topup["id"],
    )
    credit_referrer_if_first_purchase(topup["user_id"])


def credit_referrer_if_first_purchase(user_id):
    count = db.query_one("SELECT COUNT(*) AS c FROM topups WHERE user_id = ? AND status = 'success'", (user_id,))["c"]
    if count != 1:
        return
    referral = db.query_one("SELECT * FROM referrals WHERE referred_id = ?", (user_id,))
    if not referral or referral["status"] == "completed":
        return
    with db.transaction() as conn:
        conn.execute(
            "UPDATE referrals SET status='completed', bonus_coins_awarded=?, completed_at=? WHERE id=?",
            (REFERRAL_BONUS_COINS, auth.now_iso(), referral["id"]),
        )
        conn.execute("UPDATE users SET coins_balance = coins_balance + ? WHERE id = ?", (REFERRAL_BONUS_COINS, referral["referrer_id"]))
    utils.log_activity(referral["referrer_id"], "referral_credit", "system", "system", {"referred_id": user_id, "bonus_coins": REFERRAL_BONUS_COINS})
    utils.create_notification(
        referral["referrer_id"],
        "Referral bonus earned! 🎉",
        f"Someone you referred just made their first top-up — you earned {REFERRAL_BONUS_COINS} bonus coins.",
        notif_type="referral_credit",
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "FFStore/1.0"

    # ---------- low-level helpers ----------

    def log_message(self, fmt, *args):
        pass  # keep Termux console output quiet; remove this to debug

    def _cookies(self):
        c = SimpleCookie()
        c.load(self.headers.get("Cookie", ""))
        return c

    def _session_id(self):
        c = self._cookies()
        if "session_id" in c:
            return c["session_id"].value
        return None

    def current_user(self):
        return auth.get_user_from_session(self._session_id())

    def _send(self, status, body, content_type="text/html; charset=utf-8", extra_headers=None):
        body_bytes = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        # Every page here is dynamically rendered per request (balances,
        # notifications, etc.) — never let the browser serve a stale cached
        # copy after data changes or after files get updated on the server.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        for h in extra_headers or []:
            self.send_header(*h)
        self.end_headers()
        self.wfile.write(body_bytes)

    def render(self, title, body, status=200, user=None):
        csrf = auth.csrf_token_for_session(self._session_id()) if user else ""
        self._send(status, layout.page(title, body, user=user, csrf=csrf))

    def redirect(self, location, extra_headers=None):
        self.send_response(302)
        self.send_header("Location", location)
        for h in extra_headers or []:
            self.send_header(*h)
        self.end_headers()

    def set_session_cookie(self, session_id):
        return ("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age={30*24*3600}")

    def clear_session_cookie(self):
        return ("Set-Cookie", "session_id=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        parsed = parse_qs(raw, keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            return json.loads(raw)
        except ValueError:
            return {}

    def send_json(self, status, obj):
        self._send(status, json.dumps(obj), content_type="application/json")

    def ip(self):
        return utils.get_client_ip(self)

    def ua(self):
        return utils.get_user_agent(self)

    def check_csrf(self, form, session_id):
        return auth.verify_csrf(session_id, form.get("csrf_token", ""))

    # ---------- static files ----------

    def serve_static(self, path):
        rel = path[len("/public/"):]
        full = os.path.normpath(os.path.join(PUBLIC_DIR, rel))
        if not full.startswith(PUBLIC_DIR) or not os.path.isfile(full):
            self._send(404, "Not found")
            return
        ctype, _ = mimetypes.guess_type(full)
        with open(full, "rb") as f:
            self._send(200, f.read(), content_type=ctype or "application/octet-stream")

    # ---------- dispatch ----------

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path.startswith("/public/"):
            return self.serve_static(path)

        routes = {
            "/": self.get_home,
            "/register": self.get_register,
            "/login": self.get_login,
            "/faq": lambda: self.render("FAQ", views.faq_page()),
            "/terms": lambda: self.render("Terms", views.terms_page()),
            "/privacy": lambda: self.render("Privacy", views.privacy_page()),
            "/dashboard": self.get_dashboard,
            "/topup": self.get_topup,
            "/topup/paystack/callback": self.get_topup_paystack_callback,
            "/redeem": self.get_redeem,
            "/spin": self.get_spin,
            "/referrals": self.get_referrals,
            "/profile": self.get_profile,
            "/transactions": self.get_transactions,
            "/redemptions": self.get_redemptions_history,
            "/api/notifications": self.get_notifications_api,
            "/notifications": self.get_notifications_page,
            "/admin": self.get_admin_dashboard,
            "/admin/login": self.get_admin_login,
            "/admin/users": self.get_admin_users,
            "/admin/topups": self.get_admin_topups,
            "/admin/redemptions": self.get_admin_redemptions,
            "/admin/referrals": self.get_admin_referrals,
            "/admin/spins": self.get_admin_spins,
            "/admin/activity": self.get_admin_activity,
        }
        if path == "/":
            return self.get_home(qs)
        if path in routes:
            return routes[path]()

        m = ADMIN_USER_DETAIL_RE.match(path)
        if m:
            return self.get_admin_user_detail(m.group(1))

        self._send(404, layout.page("Not found", '<div class="container" style="padding:60px 16px;text-align:center;"><h1>404</h1><a href="/" class="orange">Go home</a></div>'))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/register":
            return self.post_register()
        if path == "/login":
            return self.post_login()
        if path == "/logout":
            return self.post_logout()
        if path == "/topup/simulate":
            return self.post_topup_simulate()
        if path == "/topup/paystack/start":
            return self.post_topup_paystack_start()
        if path == "/paystack/webhook":
            return self.post_paystack_webhook()
        if path == "/redeem":
            return self.post_redeem()
        if path == "/api/spin":
            return self.post_spin()
        if path == "/api/notifications/mark-read":
            return self.post_notifications_mark_read()
        if path == "/profile":
            return self.post_profile()
        if path == "/admin/login":
            return self.post_admin_login()

        m = ADMIN_REDEMPTION_RE.match(path)
        if m:
            return self.post_admin_redemption_action(m.group(1), m.group(2))

        m2 = ADMIN_USER_ACTION_RE.match(path)
        if m2:
            return self.post_admin_user_action(m2.group(1), m2.group(2))

        self._send(404, "Not found")

    # ---------- public pages ----------

    def get_home(self, qs=None):
        user = self.current_user()
        if qs and "ref" in qs:
            # Referral code is stashed in a short-lived cookie and consumed
            # at registration time.
            body = views.home_page()
            self._send(200, layout.page("FF Store", body, user=user),
                       extra_headers=[("Set-Cookie", f"ref_code={qs['ref'][0]}; Path=/; Max-Age=86400; SameSite=Lax")])
            return
        self.render("FF Store", views.home_page(), user=user)

    def get_register(self):
        self.render("Register", views.register_page())

    def get_login(self):
        self.render("Login", views.login_page())

    # ---------- auth actions ----------

    def post_register(self):
        form = self.read_form()
        name = form.get("name", "").strip()
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")
        confirm = form.get("confirm_password", "")
        ref_code = form.get("ref_code", "").strip() or self._cookies().get("ref_code", None)
        ref_code = ref_code.value if hasattr(ref_code, "value") else ref_code

        error = None
        if not name:
            error = "Name is required."
        elif not utils.valid_email(email):
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif db.query_one("SELECT id FROM users WHERE email = ?", (email,)):
            error = "An account with this email already exists."

        if error:
            return self.render("Register", views.register_page(error, name, email, ref_code or ""), status=400)

        if utils.rate_limited("register", self.ip(), max_hits=10, window_seconds=3600):
            return self.render("Register", views.register_page("Too many attempts. Try again later.", name, email), status=429)

        password_hash, salt = auth.hash_password(password)
        user_id = auth.new_id()
        referral_code = auth.generate_referral_code()

        referred_by = None
        if ref_code:
            # Restricted referrers' codes are treated exactly like an
            # invalid code — silently ignored rather than erroring, so it
            # doesn't tip off the visitor that the code specifically was blocked.
            referrer = db.query_one("SELECT id FROM users WHERE referral_code = ? AND can_refer = 1", (ref_code,))
            if referrer:
                referred_by = referrer["id"]

        db.execute(
            """INSERT INTO users (id, name, email, password_hash, password_salt, referral_code, referred_by_user_id, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, name, email, password_hash, salt, referral_code, referred_by, auth.now_iso()),
        )

        if referred_by:
            db.execute(
                "INSERT INTO referrals (id, referrer_id, referred_id, status, created_at) VALUES (?,?,?,?,?)",
                (auth.new_id(), referred_by, user_id, "pending", auth.now_iso()),
            )

        utils.log_activity(user_id, "register", self.ip(), self.ua(), {"referred_by": referred_by})

        session_id = auth.create_session(user_id, self.ip(), self.ua())
        self.redirect("/dashboard", extra_headers=[self.set_session_cookie(session_id), ("Set-Cookie", "ref_code=; Path=/; Max-Age=0")])

    def post_login(self):
        form = self.read_form()
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")

        if utils.rate_limited("login", self.ip(), max_hits=5, window_seconds=600):
            return self.render("Login", views.login_page("Too many attempts. Try again in a few minutes.", email), status=429)

        user = db.query_one("SELECT * FROM users WHERE email = ?", (email,))
        ok = user and auth.verify_password(password, user["password_hash"], user["password_salt"])

        if not ok:
            utils.log_activity(user["id"] if user else None, "failed_login", self.ip(), self.ua(), {"email": email})
            # Deliberately generic message — never reveals whether the email exists.
            return self.render("Login", views.login_page("Invalid email or password.", email), status=401)

        if not user["is_active"]:
            utils.log_activity(user["id"], "failed_login", self.ip(), self.ua(), {"email": email, "reason": "banned"})
            return self.render("Login", views.login_page("This account has been disabled. Contact support.", email), status=403)

        db.execute(
            "UPDATE users SET last_login_at=?, last_login_ip=?, last_login_user_agent=? WHERE id=?",
            (auth.now_iso(), self.ip(), self.ua(), user["id"]),
        )
        utils.log_activity(user["id"], "login", self.ip(), self.ua())
        session_id = auth.create_session(user["id"], self.ip(), self.ua())
        self.redirect("/dashboard", extra_headers=[self.set_session_cookie(session_id)])

    def post_logout(self):
        session_id = self._session_id()
        user = self.current_user()
        if user:
            utils.log_activity(user["id"], "logout", self.ip(), self.ua())
        auth.destroy_session(session_id)
        self.redirect("/", extra_headers=[self.clear_session_cookie()])

    def get_notifications_api(self):
        user = self.current_user()
        if not user:
            return self.send_json(401, {"error": "Not signed in"})
        rows = db.query(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user["id"],),
        )
        unread_count = db.query_one(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND is_read = 0", (user["id"],)
        )["c"]
        self.send_json(200, {
            "unread_count": unread_count,
            "notifications": [
                {
                    "id": n["id"],
                    "title": n["title"],
                    "message": n["message"],
                    "type": n["type"],
                    "is_read": bool(n["is_read"]),
                    "created_at": n["created_at"],
                }
                for n in rows
            ],
        })

    def post_notifications_mark_read(self):
        user = self.current_user()
        if not user:
            return self.send_json(401, {"error": "Not signed in"})
        body = self.read_json()
        if not auth.verify_csrf(self._session_id(), body.get("csrf_token", "")):
            return self.send_json(403, {"error": "Invalid CSRF token"})
        db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user["id"],))
        self.send_json(200, {"ok": True})

    def get_notifications_page(self):
        user = self.require_user()
        if not user:
            return
        rows = db.query("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (user["id"],))
        # Visiting the page itself is the "seen it" signal — mark everything read.
        db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user["id"],))
        self.render("Notifications", views.notifications_page(rows), user=user)

    # ---------- user pages (require login) ----------

    def require_user(self):
        user = self.current_user()
        if not user:
            self.redirect("/login")
            return None
        if not user["is_active"]:
            auth.destroy_session(self._session_id())
            self.redirect("/login", extra_headers=[self.clear_session_cookie()])
            return None
        return user

    def get_dashboard(self):
        user = self.require_user()
        if not user:
            return
        activity = db.query("SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 8", (user["id"],))
        self.render("Dashboard", views.dashboard_page(user, activity), user=user)

    def get_topup(self):
        user = self.require_user()
        if not user:
            return
        csrf = auth.csrf_token_for_session(self._session_id())
        self.render("Top Up", views.topup_page(user, csrf, payment.is_real_paystack_active()), user=user)

    def post_topup_simulate(self):
        """Dev-only path — instant simulated success, no real gateway.
        Automatically unavailable once real Paystack keys are configured
        (the template hides this button, and this handler double-checks
        server-side too, since hiding a button is not access control)."""
        user = self.require_user()
        if not user:
            return
        if payment.is_real_paystack_active():
            self._send(403, "Development top-up is disabled — real Paystack is configured.")
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return
        if utils.rate_limited("manual_topup", self.ip(), max_hits=30, window_seconds=3600):
            self._send(429, "Too many top-up attempts. Try again later.")
            return

        try:
            coins = int(form.get("coins", "0"))
        except ValueError:
            coins = 0
        if coins < 10:
            self.redirect("/topup")
            return

        amount_naira = coins * NAIRA_PER_COIN
        reference = f"DEV-TOPUP-{auth.new_id()[:8].upper()}"

        db.execute(
            """INSERT INTO topups (id, user_id, coins, amount_naira, payment_method, reference, status, ip_address, user_agent, created_at)
               VALUES (?,?,?,?,?,?,'pending',?,?,?)""",
            (auth.new_id(), user["id"], coins, amount_naira, "manual", reference, self.ip(), self.ua(), auth.now_iso()),
        )
        credit_topup(reference, source="manual_topup")
        self.redirect("/dashboard?topup=success")

    def post_topup_paystack_start(self):
        """Real payment path — creates a pending topup, asks Paystack for a
        hosted checkout URL, then redirects the user's browser there. Coins
        are only ever credited later, once verified (see the callback and
        webhook handlers below) — never at this step."""
        user = self.require_user()
        if not user:
            return
        if not payment.is_real_paystack_active():
            self._send(403, "Paystack is not configured on this server.")
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return
        if utils.rate_limited("manual_topup", self.ip(), max_hits=30, window_seconds=3600):
            self._send(429, "Too many top-up attempts. Try again later.")
            return

        try:
            coins = int(form.get("coins", "0"))
        except ValueError:
            coins = 0
        if coins < 10:
            self.redirect("/topup")
            return

        amount_naira = coins * NAIRA_PER_COIN
        reference = f"ff_{auth.new_id()}"
        callback_url = f"{PUBLIC_BASE_URL}/topup/paystack/callback"

        db.execute(
            """INSERT INTO topups (id, user_id, coins, amount_naira, payment_method, reference, status, ip_address, user_agent, created_at)
               VALUES (?,?,?,?,'paystack',?,'pending',?,?,?)""",
            (auth.new_id(), user["id"], coins, amount_naira, reference, self.ip(), self.ua(), auth.now_iso()),
        )

        result = payment.active_provider.initialize_payment(
            coins=coins, amount_naira=amount_naira, user_email=user["email"], callback_url=callback_url, reference=reference,
        )
        if not result.get("authorization_url"):
            self._send(502, "Could not start payment with Paystack. Please try again shortly.")
            return

        self.redirect(result["authorization_url"])

    def get_topup_paystack_callback(self):
        """Paystack redirects the user's browser back here after they pay
        (or cancel). We NEVER trust this redirect on its own — we always
        re-verify the transaction directly against Paystack's API before
        crediting anything."""
        user = self.require_user()
        if not user:
            return
        qs = parse_qs(urlparse(self.path).query)
        reference = (qs.get("reference") or qs.get("trxref") or [None])[0]
        if not reference:
            return self.redirect("/dashboard?topup=failed")

        verified = payment.active_provider.verify_payment(reference)
        if verified.get("status") == "success":
            credit_topup(reference, source="paystack")
            return self.redirect("/dashboard?topup=success")

        db.execute("UPDATE topups SET status = 'failed' WHERE reference = ? AND status = 'pending'", (reference,))
        self.redirect("/dashboard?topup=failed")

    def post_paystack_webhook(self):
        """Server-to-server callback from Paystack. Also verifies via the
        API rather than trusting the payload directly, and is idempotent
        (safe to fire even if the browser callback already credited the
        same reference) — this exists as a safety net for cases where the
        user closes their browser before the redirect completes."""
        secret = os.environ.get("PAYSTACK_SECRET_KEY", "").strip()
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b""

        signature = self.headers.get("X-Paystack-Signature", "")
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha512).hexdigest()
        if not secret or not hmac.compare_digest(signature, expected):
            self._send(401, "Invalid signature")
            return

        try:
            event = json.loads(raw_body.decode("utf-8"))
        except ValueError:
            self._send(400, "Bad payload")
            return

        if event.get("event") == "charge.success":
            reference = event.get("data", {}).get("reference")
            if reference:
                verified = payment.active_provider.verify_payment(reference)
                if verified.get("status") == "success":
                    credit_topup(reference, source="paystack")

        self.send_json(200, {"ok": True})

    def get_redeem(self):
        user = self.require_user()
        if not user:
            return
        csrf = auth.csrf_token_for_session(self._session_id())
        self.render("Redeem", views.redeem_page(user, csrf), user=user)


    def post_redeem(self):
        user = self.require_user()
        if not user:
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return
        if utils.rate_limited("redeem", user["id"], max_hits=20, window_seconds=3600):
            csrf = auth.csrf_token_for_session(session_id)
            return self.render("Redeem", views.redeem_page(user, csrf, "Too many redemption attempts. Try again later."), status=429, user=user)

        uid = form.get("uid", "").strip()
        try:
            coins = int(form.get("coins", "0"))
        except ValueError:
            coins = 0

        csrf = auth.csrf_token_for_session(session_id)
        if not utils.valid_uid(uid):
            return self.render("Redeem", views.redeem_page(user, csrf, "Invalid UID."), status=400, user=user)

        try:
            with db.transaction() as conn:
                row = conn.execute("SELECT coins_balance, coins_on_hold FROM users WHERE id = ?", (user["id"],)).fetchone()
                available = row["coins_balance"] - row["coins_on_hold"]
                if coins < 1 or coins > available:
                    raise ValueError(f"Insufficient coins — you have {available} available coins, this needs {coins} coins.")
                conn.execute("UPDATE users SET coins_on_hold = coins_on_hold + ? WHERE id = ?", (coins, user["id"]))
                request_id = auth.new_id()
                conn.execute(
                    """INSERT INTO redemption_requests (id, user_id, uid_submitted, coins_requested, status, ip_address, user_agent, created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (request_id, user["id"], uid, coins, "pending_approval", self.ip(), self.ua(), auth.now_iso()),
                )
        except ValueError as e:
            return self.render("Redeem", views.redeem_page(user, csrf, str(e)), status=400, user=user)

        utils.log_activity(user["id"], "redeem", self.ip(), self.ua(), {"uid": uid, "coins": coins, "request_id": request_id})
        utils.create_notification(
            user["id"],
            "Redemption requested",
            f"Your {coins} likes will be sent to UID {uid}. Waiting for admin approval — usually less than 24 hours.",
            notif_type="redemption_pending",
            related_id=request_id,
        )
        self.render("Redeem", views.redeem_success_page(uid, coins), user=user)

    def get_spin(self):
        user = self.require_user()
        if not user:
            return
        next_eligible = None
        can_spin = True
        if user["last_spin_at"]:
            from datetime import datetime, timedelta, timezone
            last = datetime.fromisoformat(user["last_spin_at"])
            next_eligible_dt = last + timedelta(hours=SPIN_COOLDOWN_HOURS)
            if next_eligible_dt > datetime.now(timezone.utc):
                can_spin = False
                next_eligible = next_eligible_dt.isoformat()
        csrf = auth.csrf_token_for_session(self._session_id())
        segments = [{"coins": s["coins"], "jackpot": bool(s.get("jackpot"))} for s in SPIN_SEGMENTS]
        self.render("Spin", views.spin_page(user, can_spin, next_eligible, segments, csrf), user=user)

    def post_spin(self):
        user = self.require_user()
        if not user:
            return
        body = self.read_json()
        session_id = self._session_id()
        if not auth.verify_csrf(session_id, body.get("csrf_token", "")):
            return self.send_json(403, {"error": "Invalid CSRF token"})

        if utils.rate_limited("spin", user["id"], max_hits=5, window_seconds=60):
            return self.send_json(429, {"error": "Too many spin attempts."})

        from datetime import datetime, timedelta, timezone
        if user["last_spin_at"]:
            last = datetime.fromisoformat(user["last_spin_at"])
            next_eligible = last + timedelta(hours=SPIN_COOLDOWN_HOURS)
            if next_eligible > datetime.now(timezone.utc):
                return self.send_json(429, {"error": "You've already used today's free spin.", "next_eligible_at": next_eligible.isoformat()})

        index, segment = pick_weighted_segment()
        is_jackpot = bool(segment.get("jackpot"))

        with db.transaction() as conn:
            conn.execute("UPDATE users SET coins_balance = coins_balance + ?, last_spin_at = ? WHERE id = ?",
                         (segment["coins"], auth.now_iso(), user["id"]))
            conn.execute(
                "INSERT INTO spin_logs (id, user_id, prize_coins, is_jackpot, ip_address, user_agent, created_at) VALUES (?,?,?,?,?,?,?)",
                (auth.new_id(), user["id"], segment["coins"], int(is_jackpot), self.ip(), self.ua(), auth.now_iso()),
            )

        utils.log_activity(user["id"], "spin", self.ip(), self.ua(), {"prize_coins": segment["coins"], "is_jackpot": is_jackpot})
        self.send_json(200, {"slice_index": index, "prize_coins": segment["coins"], "is_jackpot": is_jackpot})

    def get_referrals(self):
        user = self.require_user()
        if not user:
            return
        rows = db.query(
            """SELECT r.*, u.name, u.email FROM referrals r JOIN users u ON u.id = r.referred_id
               WHERE r.referrer_id = ? ORDER BY r.created_at DESC""",
            (user["id"],),
        )
        completed = [r for r in rows if r["status"] == "completed"]
        bonus_coins = sum(r["bonus_coins_awarded"] for r in completed)
        self.render(
            "Referrals",
            views.referrals_page(user, rows, len(rows), len(completed), len(rows) - len(completed), bonus_coins),
            user=user,
        )

    def get_profile(self):
        user = self.require_user()
        if not user:
            return
        csrf = auth.csrf_token_for_session(self._session_id())
        self.render("Profile", views.profile_page(user, csrf=csrf), user=user)

    def post_profile(self):
        user = self.require_user()
        if not user:
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return
        name = form.get("name", "").strip()
        if name:
            db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user["id"]))
            utils.log_activity(user["id"], "profile_update", self.ip(), self.ua(), {"name": name})
        user = self.current_user()
        csrf = auth.csrf_token_for_session(session_id)
        self.render("Profile", views.profile_page(user, "Saved.", csrf), user=user)

    def get_transactions(self):
        user = self.require_user()
        if not user:
            return
        rows = db.query("SELECT * FROM topups WHERE user_id = ? ORDER BY created_at DESC", (user["id"],))
        rows_html = "".join(
            f"<tr><td class='ash'>{t['created_at'][:19]}</td><td class='gold'>{t['coins']}</td><td>₦{t['amount_naira']:,}</td><td>{t['payment_method']}</td><td class='ash'>{t['reference']}</td><td class='status-fulfilled'>{t['status']}</td></tr>"
            for t in rows
        )
        self.render("Transaction History", views.history_page("Transaction History", rows_html, ["Date", "Coins", "Amount", "Method", "Reference", "Status"]), user=user)

    def get_redemptions_history(self):
        user = self.require_user()
        if not user:
            return
        rows = db.query("SELECT * FROM redemption_requests WHERE user_id = ? ORDER BY created_at DESC", (user["id"],))
        rows_html = "".join(
            f"<tr><td style='font-family:monospace;'>{r['uid_submitted']}</td><td class='gold'>{r['coins_requested']}</td><td class='status-{'pending' if r['status']=='pending_approval' else r['status']}'>{r['status']}</td><td class='ash'>{r['created_at'][:19]}</td><td class='ash'>{(r['resolved_at'] or '')[:19]}</td></tr>"
            for r in rows
        )
        self.render("Redemption History", views.history_page("Redemption History", rows_html, ["UID", "Coins", "Status", "Requested", "Resolved"]), user=user)

    # ---------- admin ----------

    def require_admin(self):
        user = self.current_user()
        if not user or not user["is_admin"]:
            self.redirect("/admin/login")
            return None
        if not user["is_active"]:
            auth.destroy_session(self._session_id())
            self.redirect("/admin/login", extra_headers=[self.clear_session_cookie()])
            return None
        return user

    def get_admin_login(self):
        self.render("Admin Login", views.admin_login_page())

    def post_admin_login(self):
        form = self.read_form()
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")

        if utils.rate_limited("admin_login", self.ip(), max_hits=5, window_seconds=600):
            return self.render("Admin Login", views.admin_login_page("Too many attempts. Try again later."), status=429)

        user = db.query_one("SELECT * FROM users WHERE email = ? AND is_admin = 1", (email,))
        ok = user and auth.verify_password(password, user["password_hash"], user["password_salt"])
        if not ok:
            return self.render("Admin Login", views.admin_login_page("Invalid credentials."), status=401)
        if not user["is_active"]:
            return self.render("Admin Login", views.admin_login_page("This account has been disabled."), status=403)

        utils.log_activity(user["id"], "admin_login", self.ip(), self.ua())
        session_id = auth.create_session(user["id"], self.ip(), self.ua())
        self.redirect("/admin", extra_headers=[self.set_session_cookie(session_id)])

    def get_admin_dashboard(self):
        admin = self.require_admin()
        if not admin:
            return
        revenue = db.query_one("SELECT COALESCE(SUM(amount_naira),0) AS t FROM topups WHERE status='success'")["t"]
        coins_sold = db.query_one("SELECT COALESCE(SUM(coins),0) AS t FROM topups WHERE status='success'")["t"]
        coins_redeemed = db.query_one("SELECT COALESCE(SUM(coins_requested),0) AS t FROM redemption_requests WHERE status='fulfilled'")["t"]
        on_hold = db.query_one("SELECT COALESCE(SUM(coins_on_hold),0) AS t FROM users")["t"]
        pending = db.query_one("SELECT COUNT(*) AS c FROM redemption_requests WHERE status='pending_approval'")["c"]
        total_users = db.query_one("SELECT COUNT(*) AS c FROM users")["c"]
        total_referrals = db.query_one("SELECT COUNT(*) AS c FROM referrals")["c"]
        jackpots = db.query_one("SELECT COUNT(*) AS c FROM spin_logs WHERE is_jackpot=1")["c"]

        from datetime import datetime, timedelta, timezone
        day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        dau = db.query_one(
            "SELECT COUNT(DISTINCT user_id) AS c FROM activity_logs WHERE user_id IS NOT NULL AND created_at >= ?", (day_ago,)
        )["c"]
        mau = db.query_one(
            "SELECT COUNT(DISTINCT user_id) AS c FROM activity_logs WHERE user_id IS NOT NULL AND created_at >= ?", (month_ago,)
        )["c"]

        stats = {
            "Total users": total_users,
            "Active today (DAU)": dau,
            "Active this month (MAU)": mau,
            "Revenue (simulated)": f"₦{revenue:,}",
            "Coins sold": coins_sold,
            "Coins redeemed": coins_redeemed,
            "Coins on hold": on_hold,
            "Pending redemptions": pending,
            "Total referrals": total_referrals,
            "Jackpot wins": jackpots,
        }
        self.render("Admin", views.admin_dashboard_page(stats), user=admin)

    def get_admin_users(self):
        admin = self.require_admin()
        if not admin:
            return
        users = db.query("SELECT * FROM users ORDER BY created_at DESC")
        self.render("Admin Users", views.admin_users_page(users), user=admin)

    def get_admin_user_detail(self, user_id):
        admin = self.require_admin()
        if not admin:
            return
        target = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not target:
            self.redirect("/admin/users")
            return

        topups = db.query("SELECT * FROM topups WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
        redemptions = db.query("SELECT * FROM redemption_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
        referrals_given = db.query(
            """SELECT r.*, u.email AS referred_email, u.last_login_ip AS referred_ip
               FROM referrals r JOIN users u ON u.id = r.referred_id
               WHERE r.referrer_id = ? ORDER BY r.created_at DESC""",
            (user_id,),
        )
        referral_received = db.query(
            """SELECT r.*, u.email AS referrer_email, u.last_login_ip AS referrer_ip
               FROM referrals r JOIN users u ON u.id = r.referrer_id
               WHERE r.referred_id = ?""",
            (user_id,),
        )
        spins = db.query("SELECT * FROM spin_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
        activity = db.query("SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 30", (user_id,))
        csrf = auth.csrf_token_for_session(self._session_id())

        self.render(
            f"User: {target['email']}",
            views.admin_user_detail_page(target, topups, redemptions, referrals_given, referral_received, spins, activity, csrf),
            user=admin,
        )

    def get_admin_topups(self):
        admin = self.require_admin()
        if not admin:
            return
        rows = db.query("""SELECT t.*, u.email FROM topups t JOIN users u ON u.id = t.user_id ORDER BY t.created_at DESC""")
        self.render("Admin Top-ups", views.admin_topups_page(rows), user=admin)

    def get_admin_redemptions(self):
        admin = self.require_admin()
        if not admin:
            return
        rows = db.query("""SELECT r.*, u.email FROM redemption_requests r JOIN users u ON u.id = r.user_id ORDER BY r.created_at DESC""")
        csrf = auth.csrf_token_for_session(self._session_id())
        self.render("Admin Redemptions", views.admin_redemptions_page(rows, csrf), user=admin)

    def post_admin_redemption_action(self, request_id, action):
        admin = self.require_admin()
        if not admin:
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return

        req = db.query_one("SELECT * FROM redemption_requests WHERE id = ?", (request_id,))
        if not req or req["status"] != "pending_approval":
            self.redirect("/admin/redemptions")
            return

        with db.transaction() as conn:
            if action == "approve":
                conn.execute("UPDATE users SET coins_balance = coins_balance - ?, coins_on_hold = coins_on_hold - ? WHERE id = ?",
                             (req["coins_requested"], req["coins_requested"], req["user_id"]))
                conn.execute(
                    "UPDATE redemption_requests SET status='fulfilled', resolved_at=?, resolved_by_admin_id=? WHERE id=?",
                    (auth.now_iso(), admin["id"], request_id),
                )
                log_action = "admin_approve_redemption"
            else:
                conn.execute("UPDATE users SET coins_on_hold = coins_on_hold - ? WHERE id = ?", (req["coins_requested"], req["user_id"]))
                conn.execute(
                    "UPDATE redemption_requests SET status='rejected', resolved_at=?, resolved_by_admin_id=? WHERE id=?",
                    (auth.now_iso(), admin["id"], request_id),
                )
                log_action = "admin_reject_redemption"

        if action == "approve":
            utils.create_notification(
                req["user_id"],
                "Likes delivered! 🎉",
                f"Your {req['coins_requested']} likes has been approved and sent to your UID {req['uid_submitted']}.",
                notif_type="redemption_fulfilled",
                related_id=request_id,
            )
        else:
            utils.create_notification(
                req["user_id"],
                "Redemption rejected",
                f"Your request for {req['coins_requested']} likes to UID {req['uid_submitted']} was rejected. Your coins have been returned to your balance.",
                notif_type="redemption_rejected",
                related_id=request_id,
            )

        utils.log_activity(admin["id"], log_action, self.ip(), self.ua(), {"request_id": request_id, "target_user_id": req["user_id"], "coins": req["coins_requested"]})
        self.redirect("/admin/redemptions")

    def post_admin_user_action(self, user_id, action):
        admin = self.require_admin()
        if not admin:
            return
        session_id = self._session_id()
        form = self.read_form()
        if not self.check_csrf(form, session_id):
            self._send(403, "Invalid CSRF token")
            return

        target = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not target:
            self.redirect("/admin/users")
            return

        if action == "ban":
            db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
            # Banning immediately kills any active sessions too, not just future logins.
            db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            log_action = "admin_ban_user"
        elif action == "unban":
            db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
            log_action = "admin_unban_user"
        elif action == "restrict-referral":
            db.execute("UPDATE users SET can_refer = 0 WHERE id = ?", (user_id,))
            log_action = "admin_restrict_referral"
            utils.create_notification(
                user_id,
                "Referral rewards restricted",
                "Your account has been restricted from earning referral rewards. Contact support if you believe this is a mistake.",
                notif_type="referral_restricted",
            )
        else:  # allow-referral
            db.execute("UPDATE users SET can_refer = 1 WHERE id = ?", (user_id,))
            log_action = "admin_allow_referral"
            utils.create_notification(
                user_id,
                "Referral access restored",
                "Your account can once again earn referral rewards.",
                notif_type="referral_allowed",
            )

        utils.log_activity(admin["id"], log_action, self.ip(), self.ua(), {"target_user_id": user_id, "target_email": target["email"]})
        self.redirect(f"/admin/users/{user_id}")

    def get_admin_referrals(self):
        admin = self.require_admin()
        if not admin:
            return
        rows = db.query(
            """SELECT r.*, ru.email AS referrer_email, ru.last_login_ip AS referrer_ip,
                      rd.email AS referred_email, rd.last_login_ip AS referred_ip
               FROM referrals r
               JOIN users ru ON ru.id = r.referrer_id
               JOIN users rd ON rd.id = r.referred_id
               ORDER BY r.created_at DESC"""
        )
        self.render("Admin Referrals", views.admin_referrals_page(rows), user=admin)

    def get_admin_spins(self):
        admin = self.require_admin()
        if not admin:
            return
        rows = db.query("""SELECT s.*, u.email FROM spin_logs s JOIN users u ON u.id = s.user_id ORDER BY s.created_at DESC LIMIT 200""")
        self.render("Admin Spins", views.admin_spins_page(rows), user=admin)

    def get_admin_activity(self):
        admin = self.require_admin()
        if not admin:
            return
        rows = db.query("""SELECT a.*, u.email FROM activity_logs a LEFT JOIN users u ON u.id = a.user_id ORDER BY a.created_at DESC LIMIT 300""")
        self.render("Admin Activity Log", views.admin_activity_page(rows), user=admin)


def main():
    db.init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✅ FF Likes Store (local dev) running at http://127.0.0.1:{PORT}")
    print("   To make a user an admin, run: python make_admin.py <email>")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
