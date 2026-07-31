def escape(s):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


NAV_LINKS = [
    ("/dashboard", "Dashboard"),
    ("/topup", "Top Up"),
    ("/redeem", "Redeem"),
    ("/spin", "Spin"),
    ("/referrals", "Referrals"),
]


def render_nav(user):
    if not user:
        return """
        <nav class="topnav"><div class="inner">
          <a href="/" class="logo">FF<span>STORE</span></a>
          <a href="/login" class="btn-blaze small">Sign in</a>
        </div></nav>"""

    links_html = "".join(f'<a href="{href}">{label}</a>' for href, label in NAV_LINKS)
    admin_link = '<a href="/admin">Admin</a>' if user["is_admin"] else ""
    bell = """
    <a href="/notifications" style="position:relative;padding:4px;display:inline-flex;">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffd24c" stroke-width="2">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span id="notif-badge" style="display:none;position:absolute;top:-4px;right:-4px;background:var(--ff-red);color:#fff;font-size:0.65rem;font-weight:700;border-radius:999px;min-width:16px;height:16px;line-height:16px;text-align:center;padding:0 3px;"></span>
    </a>"""
    return f"""
    <nav class="topnav">
      <div class="inner">
        <a href="/" class="logo">FF<span>STORE</span></a>
        <div style="display:flex;align-items:center;gap:14px;">
          <div class="nav-links">{links_html}{admin_link}</div>
          {bell}
          <span class="balance-pill">{user['coins_balance']} coins</span>
          <form method="POST" action="/logout" style="margin:0;">
            <button type="submit" class="btn-outline" style="font-size:0.75rem;padding:6px 10px;">Sign out</button>
          </form>
        </div>
      </div>
      <div class="mobile-links">{links_html}</div>
    </nav>"""


def page(title, body, user=None, extra_head="", csrf=""):
    notif_script = f'<script>window.CSRF_TOKEN = "{csrf}";</script><script src="/public/js/notifications.js"></script>' if user else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{escape(title)} — FF Store</title>
<link rel="stylesheet" href="/public/css/style.css" />
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
{extra_head}
</head>
<body>
{render_nav(user)}
<main>
{body}
</main>
{notif_script}
</body>
</html>"""
