# FF Likes Store — Local Development Version

Pure Python standard library only. No Flask, no Paystack, no Google OAuth,
no PostgreSQL, no pip packages at all. Runs entirely locally in Termux with
just `python app.py`.

**This has been run and tested end-to-end** — registration, login, coin
top-up (simulated), the two-step redeem-with-hold flow, insufficient-balance
rejection, the weighted spin wheel with cooldown enforcement, referral
crediting on first purchase, admin approve/reject, and CSRF rejection all
passed real requests against a running instance of this exact code before
being packaged.

## Running it

```bash
cd freefire-likes-store
python app.py
```

Open `http://127.0.0.1:8000` in your browser. That's it — SQLite creates
`data/store.db` automatically on first run.

## Becoming an admin

There's no signup checkbox for admin — register a normal account through
the site first, then run:

```bash
python make_admin.py you@example.com
```

Sign in at `/admin/login` with the same password afterward.

## What's real vs simulated

- **Payments are simulated.** The Top Up page has a "Simulate Successful
  Top Up" button instead of real Paystack checkout — coins are credited
  immediately, clearly labeled as a dev transaction (`DEV-TOPUP-XXXX`
  reference). See `payment.py` — it's built as a `PaymentProvider`
  abstraction specifically so a real Paystack provider can be dropped in
  later without touching wallet/hold/referral logic anywhere else.
- **Auth is real email/password**, hashed with PBKDF2-HMAC-SHA256
  (260,000 iterations) and a random salt per user — never stored in
  plaintext, never logged.
- **Sessions are real**, stored server-side in SQLite (not Flask sessions),
  with HttpOnly/SameSite cookies and expiry.
- **CSRF protection is real** — every state-changing form carries a token
  derived from the session ID via HMAC, verified server-side.
- **Rate limiting is real**, backed by a SQLite table (login attempts,
  registration, redemption requests, spins, admin login).

## Project structure

```
app.py          — HTTP server (http.server), routing, all business logic
db.py           — SQLite connection + transaction helper
auth.py         — password hashing, sessions, CSRF tokens
utils.py        — IP/user-agent extraction, activity logging, rate limiting
payment.py      — payment provider abstraction (dev simulator today)
layout.py       — shared page shell (nav, Tailwind CDN, Garena FF theme)
views.py        — every page's HTML, generated as plain Python strings
schema.sql      — full SQLite schema
make_admin.py   — CLI to promote a user to admin
public/css/     — the Garena FF stylesheet
```

## Known gaps (by design, for a first local-dev pass)

- No pagination on admin tables yet — fine at low row counts, worth adding
  before real scale.
- No CSV export on admin tables yet.
- Self-referral/abuse detection is basic (referrer/referred can't be the
  same account; no IP-clustering heuristics yet — the spec explicitly
  warned against auto-banning shared IPs, so this needs a human reviewing
  the activity log rather than an automatic rule).
- SQLite is genuinely fine for local dev and even small real deployments,
  but if this ever needs to handle concurrent writes at scale, that's the
  point to reconsider (Postgres, etc.) — not before.

## Next step when you're ready for the real thing

Swap `DevelopmentPaymentProvider` in `payment.py` for a real Paystack
provider implementing the same `initialize_payment`/`verify_payment`
interface, and swap email/password (or add alongside it) for Google OAuth
if you still want that — the wallet, hold, referral, and admin logic
underneath doesn't need to change for either of those.

## Hosting for real, with real Paystack

**A phone running Termux isn't a real host** — it needs to stay on, connected, and reachable at a fixed address 24/7, which phones aren't built for. For a real launch, run this on a small VPS or PaaS instead (Render, Railway, a $5 DigitalOcean droplet, etc.) — the code itself doesn't change, only where it runs.

### 1. Get real Paystack keys
Paystack dashboard → Settings → API Keys & Webhooks. Copy the **secret key** and **public key** (use test-mode keys first).

### 2. Set environment variables on your host
Copy `.env.example` to `.env` and fill in:
```
PAYSTACK_SECRET_KEY=sk_live_xxxxx
PAYSTACK_PUBLIC_KEY=pk_live_xxxxx
PUBLIC_BASE_URL=https://yourdomain.com
PORT=8000
```
The moment `PAYSTACK_SECRET_KEY` is set, the whole app switches from the dev top-up simulator to real Paystack automatically — no code changes needed. The "Simulate Successful Top Up" button disappears and is also blocked server-side if somehow requested.

### 3. Set the webhook URL in Paystack
Paystack dashboard → Settings → API Keys & Webhooks → Webhook URL:
```
https://yourdomain.com/paystack/webhook
```
This is a safety net — real crediting also happens the moment the user is redirected back after paying (`/topup/paystack/callback`), verified directly against Paystack's API either way. The webhook just makes sure a payment still gets credited even if someone closes their browser mid-redirect.

### 4. Put it behind HTTPS
This app serves plain HTTP itself — put a reverse proxy in front of it for TLS. [Caddy](https://caddyserver.com) is the simplest option (automatic HTTPS, ~3 lines of config):
```
yourdomain.com {
    reverse_proxy 127.0.0.1:8000
}
```
Then keep the app itself running with something that restarts it if it crashes, e.g. a systemd service:
```ini
[Unit]
Description=FF Likes Store
After=network.target

[Service]
WorkingDirectory=/path/to/ffpy
ExecStart=/usr/bin/python3 app.py
Restart=always
EnvironmentFile=/path/to/ffpy/.env

[Install]
WantedBy=multi-user.target
```

### 5. Test with Paystack test-mode keys first
Use Paystack's test card numbers before ever switching to live keys. Confirm a successful payment credits coins once, and a declined/cancelled payment doesn't credit anything.

## Deploying to Fly.io (recommended free host)

Chosen because it gives real persistent storage for `data/store.db` — unlike most free static/serverless hosts, which would silently wipe wallet balances on every redeploy. `Dockerfile` and `fly.toml` are already set up for this.

```bash
# 1. Install flyctl (one-time)
curl -L https://fly.io/install.sh | sh

# 2. Log in
flyctl auth login

# 3. Launch (creates the app on Fly's side — say NOT to overwrite fly.toml if asked, it's already configured)
flyctl launch --no-deploy

# 4. Create a persistent volume for the database (must match the region in fly.toml)
flyctl volumes create ff_data --size 1 --region lhr

# 5. Set your real secrets (never commit these to a repo)
flyctl secrets set \
  PAYSTACK_SECRET_KEY=sk_live_xxxxx \
  PAYSTACK_PUBLIC_KEY=pk_live_xxxxx \
  PUBLIC_BASE_URL=https://ff-likes-store.fly.dev

# 6. Deploy
flyctl deploy
```

Fly gives you a free `https://<app-name>.fly.dev` domain automatically — use that as `PUBLIC_BASE_URL` and as the Paystack webhook URL (`https://<app-name>.fly.dev/paystack/webhook`), or point your own domain at it later.

To promote yourself to admin once deployed:
```bash
flyctl ssh console -C "python make_admin.py your@email.com"
```
