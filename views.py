from layout import escape

NAIRA_PER_COIN = 5


def stat_card(label, value, color="text-white"):
    return f"""<div class="card"><p class="ash" style="font-size:0.8rem;">{escape(label)}</p>
    <p class="{color}" style="font-size:1.6rem;font-weight:700;margin:4px 0;">{value}</p></div>"""


# ---------- PUBLIC PAGES ----------

def home_page():
    return f"""
<section class="container hero">
  <p class="gold" style="letter-spacing:0.3em;font-size:0.75rem;">FREE FIRE PROFILE BOOST</p>
  <h1>Top up coins.<br><span class="blaze-text">Boost your likes.</span></h1>
  <p class="ash" style="max-width:480px;margin:0 auto 28px;">1 coin = 1 like. 100 coins = ₦500. This local build uses a development top-up simulator instead of real payments — build and test the full flow before wiring up Paystack.</p>
  <a href="/register" class="btn-blaze" style="font-size:1.1rem;">Get Started</a>
</section>

<section class="container" style="padding:40px 16px;">
  <h2 style="text-align:center;margin-bottom:24px;">Simple Pricing</h2>
  <div class="grid grid-3">
    <div class="card" style="text-align:center;"><p class="gold" style="font-size:2rem;font-weight:700;margin:0;">100</p><p class="ash" style="font-size:0.85rem;">coins / likes</p><p class="display" style="font-size:1.5rem;">₦500</p></div>
    <div class="card" style="text-align:center;"><p class="gold" style="font-size:2rem;font-weight:700;margin:0;">500</p><p class="ash" style="font-size:0.85rem;">coins / likes</p><p class="display" style="font-size:1.5rem;">₦2,500</p></div>
    <div class="card" style="text-align:center;"><p class="gold" style="font-size:2rem;font-weight:700;margin:0;">1000</p><p class="ash" style="font-size:0.85rem;">coins / likes</p><p class="display" style="font-size:1.5rem;">₦5,000</p></div>
  </div>
</section>

<section class="container" style="padding:40px 16px;">
  <h2 style="text-align:center;margin-bottom:24px;">How It Works</h2>
  <div class="grid grid-4">
    <div class="card"><h3 class="orange" style="font-size:1rem;">Sign up</h3><p class="ash" style="font-size:0.9rem;">Create an account with email and password.</p></div>
    <div class="card"><h3 class="orange" style="font-size:1rem;">Top up</h3><p class="ash" style="font-size:0.9rem;">Add coins to your wallet. 1 coin = 1 like.</p></div>
    <div class="card"><h3 class="orange" style="font-size:1rem;">Redeem</h3><p class="ash" style="font-size:0.9rem;">Enter your UID, choose how many coins to spend.</p></div>
    <div class="card"><h3 class="orange" style="font-size:1rem;">We deliver</h3><p class="ash" style="font-size:0.9rem;">Our team sends the likes to your account in-game.</p></div>
  </div>
</section>

<section class="container" style="padding:40px 16px;text-align:center;">
  <div class="card">
    <h2 style="margin-bottom:8px;">🎡 Free Daily Spin</h2>
    <p class="ash" style="margin-bottom:16px;">Every account gets one free spin every 24 hours — win up to 50 bonus coins.</p>
    <a href="/register" class="btn-blaze">Sign up to Spin</a>
  </div>
</section>

<footer class="ash" style="text-align:center;font-size:0.75rem;padding:40px 16px;border-top:1px solid rgba(255,106,0,0.1);">
  © 2026 FF Store — local development build. Not affiliated with Garena or Free Fire.
</footer>
"""


def register_page(error=None, name="", email="", ref_code=""):
    error_html = f'<p class="error-text">{escape(error)}</p>' if error else ""
    return f"""
<div class="container-sm" style="padding:60px 16px;">
  <h1>Create Account</h1>
  <p class="ash" style="margin-bottom:20px;">Sign up with your email — no external accounts needed.</p>
  <form method="POST" action="/register" class="card">
    <label class="field-label">Full name</label>
    <input class="input-ff" name="name" value="{escape(name)}" required />
    <label class="field-label" style="margin-top:12px;">Email</label>
    <input class="input-ff" type="email" name="email" value="{escape(email)}" required />
    <label class="field-label" style="margin-top:12px;">Password</label>
    <input class="input-ff" type="password" name="password" minlength="8" required />
    <label class="field-label" style="margin-top:12px;">Confirm password</label>
    <input class="input-ff" type="password" name="confirm_password" minlength="8" required />
    <label class="field-label" style="margin-top:12px;">Referral code (optional)</label>
    <input class="input-ff" name="ref_code" value="{escape(ref_code)}" placeholder="REF-ABC123" />
    {error_html}
    <button type="submit" class="btn-blaze" style="width:100%;margin-top:20px;">Create Account</button>
  </form>
  <p class="ash" style="margin-top:16px;font-size:0.85rem;">Already have an account? <a href="/login" class="orange">Sign in</a></p>
</div>
"""


def login_page(error=None, email=""):
    error_html = f'<p class="error-text">{escape(error)}</p>' if error else ""
    return f"""
<div class="container-sm" style="padding:80px 16px;">
  <h1>Sign In</h1>
  <form method="POST" action="/login" class="card">
    <label class="field-label">Email</label>
    <input class="input-ff" type="email" name="email" value="{escape(email)}" required />
    <label class="field-label" style="margin-top:12px;">Password</label>
    <input class="input-ff" type="password" name="password" required />
    {error_html}
    <button type="submit" class="btn-blaze" style="width:100%;margin-top:20px;">Sign In</button>
  </form>
  <p class="ash" style="margin-top:16px;font-size:0.85rem;">No account? <a href="/register" class="orange">Register</a></p>
</div>
"""


def faq_page():
    items = [
        ("How do coins work?", "1 coin = 1 Free Fire like. 100 coins costs ₦500."),
        ("How do I top up?", "This local build uses a development top-up simulator instead of real payments — click 'Simulate Successful Top Up' on the Top Up page."),
        ("Why are my coins put 'on hold'?", "When you submit a redemption request, those coins are reserved so you can't spend them twice while it's pending. They're only actually deducted once an admin approves the request."),
        ("How long does redemption take?", "It depends on manual review — you'll see the status change from Pending to Fulfilled once it's done."),
        ("How does the spin wheel work?", "One free spin every 24 hours, tracked server-side. Prizes range from 1 to 15 coins, with a rare 50-coin jackpot at 0.1% odds."),
        ("How do referrals work?", "Share your referral link. When someone you refer signs up and completes their first top-up, you get 50 bonus coins."),
    ]
    rows = "".join(f'<div class="card" style="margin-bottom:12px;"><h3 style="font-size:1rem;" class="orange">{escape(q)}</h3><p class="ash" style="font-size:0.9rem;margin-top:6px;">{escape(a)}</p></div>' for q, a in items)
    return f"""<div class="container-sm" style="padding:50px 16px;"><h1>FAQ</h1><p class="ash" style="margin-bottom:20px;">This is an independent service and is not affiliated with Garena or Free Fire.</p>{rows}</div>"""


def terms_page():
    return """<div class="container-sm" style="padding:50px 16px;"><h1>Terms of Service</h1>
    <div class="card" style="font-size:0.9rem;line-height:1.7;">
    <p class="ash">This is a development-stage document — replace with reviewed legal terms before real launch.</p>
    <p class="ash">By using this service you agree to: provide accurate account information; not attempt to abuse the referral or spin systems; understand that coins held for a pending redemption are not refundable in coin form once approved and fulfilled; understand that redemption timing depends on manual review.</p>
    </div></div>"""


def privacy_page():
    return """<div class="container-sm" style="padding:50px 16px;"><h1>Privacy Policy</h1>
    <div class="card" style="font-size:0.9rem;line-height:1.7;">
    <p class="ash">We store your name, email, a securely hashed password, and — for security and abuse-prevention purposes — the IP address and browser/device user-agent string associated with logins, top-ups, redemptions, spins, and referral activity. User-agent data identifies general browser/OS/device characteristics; it does not reveal a precise device name.</p>
    </div></div>"""


# ---------- USER PAGES ----------

def dashboard_page(user, recent_activity):
    available = user["coins_balance"] - user["coins_on_hold"]
    naira = available * NAIRA_PER_COIN
    activity_rows = "".join(
        f'<div class="card" style="padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;font-size:0.85rem;"><span>{escape(a["action"])}</span><span class="ash">{escape(a["created_at"][:19])}</span></div>'
        for a in recent_activity
    ) or '<p class="ash" style="font-size:0.9rem;">No recent activity yet.</p>'

    return f"""
<div class="container" style="padding:40px 16px;">
  <h1 style="margin-bottom:24px;">Welcome back, {escape(user['name'].split(' ')[0])}</h1>
  <div class="grid grid-3" style="margin-bottom:24px;">
    {stat_card("Available coins", available, "gold")}
    {stat_card("On hold (pending)", user['coins_on_hold'])}
    {stat_card("Naira equivalent", f"₦{naira:,}")}
  </div>
  <div class="grid grid-4" style="margin-bottom:24px;">
    <a href="/topup" class="card"><h3 class="orange" style="font-size:1rem;margin:0 0 4px;">Top Up</h3><p class="ash" style="font-size:0.85rem;">Add coins</p></a>
    <a href="/redeem" class="card"><h3 class="orange" style="font-size:1rem;margin:0 0 4px;">Redeem</h3><p class="ash" style="font-size:0.85rem;">Send likes to UID</p></a>
    <a href="/spin" class="card"><h3 class="orange" style="font-size:1rem;margin:0 0 4px;">Spin & Win</h3><p class="ash" style="font-size:0.85rem;">Free daily coins</p></a>
    <a href="/referrals" class="card"><h3 class="orange" style="font-size:1rem;margin:0 0 4px;">Referrals</h3><p class="ash" style="font-size:0.85rem;">Earn 50 coins</p></a>
  </div>
  <h2 style="font-size:1.1rem;margin-bottom:10px;">Recent Activity</h2>
  {activity_rows}
</div>
"""


def topup_page(user, csrf, real_paystack_active):
    if real_paystack_active:
        notice = ""
        form_action = "/topup/paystack/start"
        button_label = "Pay with Paystack"
    else:
        notice = """<div class="card" style="background:rgba(255,106,0,0.08);margin-bottom:16px;font-size:0.85rem;">
    Payment integration is currently disabled during development. Use the simulator below to test wallet functionality — this is <strong>not</strong> a real payment.
  </div>"""
        form_action = "/topup/simulate"
        button_label = "Simulate Successful Top Up"

    return f"""
<div class="container-sm" style="padding:40px 16px;">
  <h1>Top Up Coins</h1>
  <p class="ash" style="margin-bottom:12px;">1 coin = 1 like. No UID needed here — that's on the Redeem page.</p>
  {notice}
  <div class="card">
    <div class="grid grid-4" id="quick-amounts" style="margin-bottom:16px;"></div>
    <label class="field-label">Custom coin amount</label>
    <input id="coins-input" type="number" min="10" class="input-ff" value="100" />
    <div style="display:flex;justify-content:space-between;margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,106,0,0.1);">
      <span class="ash">You'll receive</span><span id="coins-out" class="gold" style="font-weight:700;">100 coins</span>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:4px;">
      <span class="ash">Price</span><span id="price-out" style="font-size:1.5rem;font-weight:700;">₦500</span>
    </div>
    <p id="error" class="error-text" style="display:none;"></p>
    <form method="POST" action="{form_action}" id="topup-form">
      <input type="hidden" name="csrf_token" value="{csrf}" />
      <input type="hidden" name="coins" id="coins-hidden" value="100" />
      <button type="submit" class="btn-blaze" style="width:100%;margin-top:20px;">{button_label}</button>
    </form>
  </div>
</div>
<script>
  const input = document.getElementById("coins-input");
  const coinsOut = document.getElementById("coins-out");
  const priceOut = document.getElementById("price-out");
  const hidden = document.getElementById("coins-hidden");
  const quickWrap = document.getElementById("quick-amounts");
  [100, 200, 500, 1000].forEach((amt) => {{
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "btn-outline"; btn.textContent = amt; btn.style.padding = "10px";
    btn.onclick = () => {{ input.value = amt; update(); }};
    quickWrap.appendChild(btn);
  }});
  function update() {{
    const coins = Number(input.value) || 0;
    coinsOut.textContent = coins + " coins";
    priceOut.textContent = "₦" + (coins * {NAIRA_PER_COIN}).toLocaleString();
    hidden.value = coins;
  }}
  input.addEventListener("input", update);
  update();
</script>
"""


def redeem_page(user, csrf, error=None):
    available = user["coins_balance"] - user["coins_on_hold"]
    error_html = f'<p class="error-text" id="server-error">{escape(error)}</p>' if error else ""
    return f"""
<div class="container-sm" style="padding:40px 16px;">
  <h1>Redeem Likes</h1>
  <p id="step-label" class="ash" style="margin-bottom:20px;">Step 1 of 2 — enter your UID</p>
  {error_html}

  <div class="card" id="step1">
    <label class="field-label">Free Fire UID</label>
    <input id="uid-input" class="input-ff" placeholder="e.g. 123456789" inputmode="numeric" />
    <p id="uid-error" class="error-text" style="display:none;"></p>
    <button type="button" id="next-btn" class="btn-blaze" style="width:100%;margin-top:20px;">Next</button>
  </div>

  <form method="POST" action="/redeem" id="step2" class="card" style="display:none;">
    <input type="hidden" name="csrf_token" value="{csrf}" />
    <input type="hidden" name="uid" id="uid-hidden" />
    <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:8px;" class="ash">
      <span>UID: <span id="uid-display"></span></span>
      <button type="button" id="change-uid" style="background:none;border:none;color:var(--ff-orange);text-decoration:underline;cursor:pointer;">Change</button>
    </div>
    <label class="field-label">Coins to redeem (1 coin = 1 like)</label>
    <input id="coins-input" name="coins" type="number" min="1" class="input-ff" value="100" />
    <p class="ash" style="font-size:0.75rem;margin-top:8px;">Available balance: {available} coins</p>
    <p id="client-error" class="error-text" style="display:none;"></p>
    <button type="submit" class="btn-blaze" style="width:100%;margin-top:20px;">Redeem</button>
  </form>
</div>
<script>
  const AVAILABLE = {available};
  const uidInput = document.getElementById("uid-input");
  const uidError = document.getElementById("uid-error");
  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");
  const stepLabel = document.getElementById("step-label");

  document.getElementById("next-btn").addEventListener("click", () => {{
    uidError.style.display = "none";
    const val = uidInput.value.trim();
    if (!/^\\d{{6,12}}$/.test(val)) {{
      uidError.textContent = "Enter a valid Free Fire UID (numbers only).";
      uidError.style.display = "block";
      return;
    }}
    document.getElementById("uid-hidden").value = val;
    document.getElementById("uid-display").textContent = val;
    step1.style.display = "none";
    step2.style.display = "block";
    stepLabel.textContent = "Step 2 of 2 — choose how many likes to redeem";
  }});

  document.getElementById("change-uid").addEventListener("click", () => {{
    step2.style.display = "none"; step1.style.display = "block";
    stepLabel.textContent = "Step 1 of 2 — enter your UID";
  }});

  document.getElementById("step2").addEventListener("submit", (e) => {{
    const coins = Number(document.getElementById("coins-input").value);
    const err = document.getElementById("client-error");
    if (coins > AVAILABLE) {{
      e.preventDefault();
      err.innerHTML = `Insufficient coins — you have ${{AVAILABLE}} coins, this needs ${{coins}}. <a href="/topup" class="gold" style="text-decoration:underline;">Top up now →</a>`;
      err.style.display = "block";
    }}
  }});
</script>
"""


def redeem_success_page(uid, coins):
    return f"""
<div class="container-sm" style="padding:80px 16px;text-align:center;">
  <div class="card">
    <h1 style="margin-bottom:8px;">Request submitted 🎉</h1>
    <p class="ash" style="margin-bottom:16px;">{coins} coins are on hold for UID {escape(uid)}. Your likes usually take less than 24 hours to be sent once approved.</p>
    <div style="background:rgba(255,210,76,0.1);border:1px solid rgba(255,210,76,0.3);border-radius:10px;padding:12px 16px;margin-bottom:20px;font-size:0.85rem;display:flex;align-items:center;justify-content:center;gap:8px;">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffd24c" stroke-width="2" style="flex-shrink:0;"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      <span>Check the <span class="gold" style="font-weight:700;">notification bell</span> at the top later to know when your likes have been sent.</span>
    </div>
    <a href="/dashboard" class="btn-blaze">Back to Dashboard</a>
  </div>
</div>"""


def spin_page(user, can_spin, next_eligible_at, segments, csrf):
    segments_json = str(segments).replace("'", '"').replace("True", "true").replace("False", "false")
    next_eligible_json = f'"{next_eligible_at}"' if next_eligible_at else "null"
    return f"""
<div class="container-sm" style="padding:40px 16px;text-align:center;">
  <h1>🎡 Spin to Win</h1>
  <p class="ash" style="margin-bottom:32px;">One free spin every 24 hours. Odds favor small wins, with a rare 50-coin jackpot.</p>
  <div class="wheel-wrap" style="position:relative;width:280px;height:280px;margin:0 auto;">
    <div class="pointer" style="position:absolute;left:50%;top:-14px;transform:translateX(-50%);z-index:10;width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:24px solid var(--ff-gold);"></div>
    <div class="wheel" id="wheel" style="width:100%;height:100%;border-radius:50%;border:4px solid var(--ff-gold);box-shadow:0 0 24px rgba(255,210,76,0.55);position:relative;overflow:hidden;"></div>
    <button id="spin-btn" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#e8352b,#ff6a00,#ffd24c);color:#000;font-weight:700;border:none;cursor:pointer;z-index:10;" {"disabled" if not can_spin else ""}>SPIN</button>
  </div>
  <p id="countdown" class="ash" style="margin-top:24px;"></p>
  <p id="result" style="margin-top:16px;font-size:1.3rem;font-weight:700;"></p>
  <p id="error" class="error-text"></p>
</div>
<script>
  const CSRF = "{csrf}";
  let segments = {segments_json};
  let canSpin = {"true" if can_spin else "false"};
  let nextEligibleAt = {next_eligible_json};
  let rotation = 0;
  const wheelEl = document.getElementById("wheel");
  const spinBtn = document.getElementById("spin-btn");
  const SLICE_COLORS = ["#FF6A00","#161618","#FFA200","#0B0B0D","#E8352B","#161618","#FF6A00","#0B0B0D","#FFA200"];

  function drawWheel() {{
    const n = segments.length, sliceAngle = 360/n;
    const gradient = segments.map((s,i) => `${{s.jackpot ? "#FFD24C" : SLICE_COLORS[i % SLICE_COLORS.length]}} ${{i*sliceAngle}}deg ${{(i+1)*sliceAngle}}deg`).join(", ");
    wheelEl.style.background = `conic-gradient(${{gradient}})`;
    segments.forEach((s,i) => {{
      const angle = i*sliceAngle + sliceAngle/2;
      const label = document.createElement("div");
      label.style.cssText = `position:absolute;inset:0;display:flex;justify-content:center;transform:rotate(${{angle}}deg);`;
      label.innerHTML = `<span style="margin-top:12px;font-weight:700;color:${{s.jackpot ? "#000" : "#fff"}}">${{s.coins}}</span>`;
      wheelEl.appendChild(label);
    }});
  }}
  drawWheel();

  function updateCountdown() {{
    if (canSpin || !nextEligibleAt) return;
    const t = setInterval(() => {{
      const diff = new Date(nextEligibleAt).getTime() - Date.now();
      if (diff <= 0) {{ document.getElementById("countdown").textContent = "Ready! Refresh the page."; clearInterval(t); return; }}
      const h = Math.floor(diff/3600000), m = Math.floor((diff%3600000)/60000), s = Math.floor((diff%60000)/1000);
      document.getElementById("countdown").innerHTML = `Next free spin in <span class="gold" style="font-weight:700;">${{h}}h ${{m}}m ${{s}}s</span>`;
    }}, 1000);
  }}
  updateCountdown();

  spinBtn.addEventListener("click", async () => {{
    if (!canSpin) return;
    spinBtn.disabled = true;
    const res = await fetch("/api/spin", {{ method: "POST", headers: {{"Content-Type":"application/json"}}, body: JSON.stringify({{csrf_token: CSRF}}) }});
    const data = await res.json();
    if (!res.ok) {{ document.getElementById("error").textContent = data.error; spinBtn.disabled = false; return; }}
    const n = segments.length, sliceAngle = 360/n;
    const targetMid = data.slice_index*sliceAngle + sliceAngle/2;
    const jitter = (Math.random()-0.5) * (sliceAngle*0.4);
    rotation += 6*360 + (360 - targetMid + jitter);
    wheelEl.style.transition = "transform 4.2s cubic-bezier(0.15,0.75,0.15,1)";
    wheelEl.style.transform = `rotate(${{rotation}}deg)`;
    setTimeout(() => {{
      const r = document.getElementById("result");
      if (data.is_jackpot) {{ r.innerHTML = "🎉 JACKPOT! +" + data.prize_coins + " coins"; r.style.color = "var(--ff-gold)"; }}
      else {{ r.textContent = "You won " + data.prize_coins + " coins!"; r.style.color = "var(--ff-orange)"; }}
    }}, 4200);
  }});
</script>
"""


def referrals_page(user, referrals, total, completed, pending, bonus_coins):
    rows = "".join(
        f'<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;margin-bottom:8px;"><span style="font-size:0.9rem;">{escape(r["name"])}</span><span style="font-size:0.75rem;font-weight:600;" class="{"gold" if r["status"]=="completed" else "ash"}">{"+" + str(r["bonus_coins_awarded"]) + " coins" if r["status"]=="completed" else "Pending first purchase"}</span></div>'
        for r in referrals
    ) or '<p class="ash" style="font-size:0.9rem;">No referrals yet — share your link above.</p>'

    return f"""
<div class="container-sm" style="padding:40px 16px;">
  <h1>Refer & Earn</h1>
  <p class="ash" style="margin-bottom:20px;">Get 50 bonus coins when someone you refer makes their first top-up.</p>
  <div class="card" style="margin-bottom:20px;">
    <label class="field-label">Your referral link</label>
    <div style="display:flex;gap:8px;">
      <input id="ref-link" class="input-ff" readonly value="http://localhost:8000/?ref={user['referral_code']}" style="font-size:0.8rem;" />
      <button id="copy-btn" type="button" class="btn-blaze small">Copy</button>
    </div>
  </div>
  <div class="grid grid-3" style="margin-bottom:24px;">
    {stat_card("Total referred", total, "gold")}
    {stat_card("Completed", completed)}
    {stat_card("Coins earned", bonus_coins, "orange")}
  </div>
  <h2 style="font-size:1.1rem;margin-bottom:10px;">Your referrals</h2>
  {rows}
</div>
<script>
  document.getElementById("copy-btn").addEventListener("click", () => {{
    navigator.clipboard.writeText(document.getElementById("ref-link").value);
    const b = document.getElementById("copy-btn"); b.textContent = "Copied!"; setTimeout(() => b.textContent = "Copy", 2000);
  }});
</script>
"""


def profile_page(user, message=None, csrf=""):
    msg_html = f'<p class="gold" style="font-size:0.85rem;margin-top:8px;">{escape(message)}</p>' if message else ""
    return f"""
<div class="container-sm" style="padding:40px 16px;">
  <h1>Profile</h1>
  <div class="card">
    <p class="ash" style="font-size:0.85rem;">Email</p>
    <p style="margin-bottom:16px;">{escape(user['email'])}</p>
    <p class="ash" style="font-size:0.85rem;">Referral code</p>
    <p style="margin-bottom:16px;">{escape(user['referral_code'])}</p>
    <p class="ash" style="font-size:0.85rem;">Joined</p>
    <p style="margin-bottom:16px;">{escape(user['created_at'][:10])}</p>
    <form method="POST" action="/profile">
      <input type="hidden" name="csrf_token" value="{csrf}" />
      <label class="field-label">Name</label>
      <input class="input-ff" name="name" value="{escape(user['name'])}" required />
      {msg_html}
      <button type="submit" class="btn-blaze" style="width:100%;margin-top:16px;">Save</button>
    </form>
  </div>
  <form method="POST" action="/logout" style="margin-top:16px;">
    <button type="submit" class="btn-outline" style="width:100%;">Sign out</button>
  </form>
</div>
"""


def history_page(title, rows_html, headers):
    header_html = "".join(f"<th>{escape(h)}</th>" for h in headers)
    return f"""
<div class="container" style="padding:40px 16px;">
  <h1 style="margin-bottom:20px;">{escape(title)}</h1>
  <div class="table-scroll">
    <table class="admin-table"><thead><tr>{header_html}</tr></thead><tbody>{rows_html or f'<tr><td colspan="{len(headers)}" class="ash" style="text-align:center;padding:20px;">Nothing here yet.</td></tr>'}</tbody></table>
  </div>
</div>"""


def notifications_page(notifications):
    if not notifications:
        rows_html = '<p class="ash" style="text-align:center;padding:40px 0;">No notifications yet.</p>'
    else:
        rows_html = "".join(
            f"""<div class="card" style="margin-bottom:10px;{'background:rgba(255,106,0,0.08);' if not n['is_read'] else ''}">
            <p style="font-weight:700;margin:0 0 4px;">{escape(n['title'])}</p>
            <p class="ash" style="font-size:0.9rem;margin:0;">{escape(n['message'])}</p>
            <p class="ash" style="font-size:0.75rem;margin:8px 0 0;">{escape(n['created_at'][:19].replace('T', ' '))}</p>
            </div>"""
            for n in notifications
        )
    return f"""
<div class="container-sm" style="padding:40px 16px;">
  <h1 style="margin-bottom:20px;">Notifications</h1>
  {rows_html}
</div>"""


# ---------- ADMIN PAGES ----------

def admin_login_page(error=None):
    error_html = f'<p class="error-text">{escape(error)}</p>' if error else ""
    return f"""
<div class="container-sm" style="padding:80px 16px;">
  <h1>Admin Login</h1>
  <form method="POST" action="/admin/login" class="card">
    <label class="field-label">Email</label>
    <input class="input-ff" type="email" name="email" required />
    <label class="field-label" style="margin-top:12px;">Password</label>
    <input class="input-ff" type="password" name="password" required />
    {error_html}
    <button type="submit" class="btn-blaze" style="width:100%;margin-top:20px;">Sign In</button>
  </form>
</div>
"""


ADMIN_NAV = """
<div class="container" style="padding-top:20px;">
  <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:0.85rem;margin-bottom:20px;" class="ash">
    <a href="/admin" class="orange">Overview</a>
    <a href="/admin/users" class="orange">Users</a>
    <a href="/admin/topups" class="orange">Top-ups</a>
    <a href="/admin/redemptions" class="orange">Redemptions</a>
    <a href="/admin/referrals" class="orange">Referrals</a>
    <a href="/admin/spins" class="orange">Spins</a>
    <a href="/admin/activity" class="orange">Activity Log</a>
  </div>
</div>"""


def admin_dashboard_page(stats):
    cards = "".join(
        stat_card(label, value, "gold" if "revenue" in label.lower() else "text-white")
        for label, value in stats.items()
    )
    return f"""{ADMIN_NAV}
<div class="container" style="padding:0 16px 40px;">
  <h1 style="margin-bottom:20px;">Admin Overview</h1>
  <div class="grid grid-4">{cards}</div>
</div>"""


def admin_users_page(users):
    rows = "".join(
        f"""<tr>
        <td><a href="/admin/users/{u['id']}" class="orange" style="text-decoration:underline;">{escape(u['name'])}</a></td>
        <td class="ash">{escape(u['email'])}</td>
        <td class="gold" style="font-weight:700;">{u['coins_balance']}</td>
        <td class="{'status-fulfilled' if u['is_active'] else 'status-rejected'}">{'Active' if u['is_active'] else 'Banned'}</td>
        <td class="{'status-fulfilled' if u['can_refer'] else 'status-pending'}">{'Allowed' if u['can_refer'] else 'Restricted'}</td>
        <td class="ash">{escape(u['created_at'][:10])}</td>
        <td><a href="/admin/users/{u['id']}" class="btn-outline" style="font-size:0.75rem;padding:4px 10px;">View</a></td>
        </tr>"""
        for u in users
    )
    body = history_page("Users", rows, ["Name", "Email", "Balance", "Status", "Referrals", "Joined", ""])
    return ADMIN_NAV + body


def admin_user_detail_page(user, topups, redemptions, referrals_given, referrals_received, spins, activity, csrf):
    def mini_table(headers, rows_html, empty_msg="Nothing here yet."):
        header_html = "".join(f"<th>{escape(h)}</th>" for h in headers)
        return f"""<div class="table-scroll"><table class="admin-table"><thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html or f'<tr><td colspan="{len(headers)}" class="ash" style="text-align:center;padding:14px;">{empty_msg}</td></tr>'}</tbody></table></div>"""

    ban_form = f"""<form method="POST" action="/admin/users/{user['id']}/{'unban' if not user['is_active'] else 'ban'}" style="display:inline;">
        <input type="hidden" name="csrf_token" value="{csrf}"/>
        <button class="btn-blaze small" style="background:{'#16a34a' if not user['is_active'] else 'var(--ff-red)'};box-shadow:none;color:#fff;margin-right:8px;">{'Unban user' if not user['is_active'] else 'Ban user'}</button>
    </form>"""
    refer_form = f"""<form method="POST" action="/admin/users/{user['id']}/{'allow-referral' if not user['can_refer'] else 'restrict-referral'}" style="display:inline;">
        <input type="hidden" name="csrf_token" value="{csrf}"/>
        <button class="btn-blaze small" style="background:{'#16a34a' if not user['can_refer'] else '#92400e'};box-shadow:none;color:#fff;">{'Allow referrals' if not user['can_refer'] else 'Restrict referrals'}</button>
    </form>"""

    topups_html = mini_table(
        ["Coins", "Amount", "Method", "Status", "IP", "Date"],
        "".join(
            f"<tr><td class='gold'>{t['coins']}</td><td>₦{t['amount_naira']:,}</td><td>{escape(t['payment_method'])}</td><td class='status-{'fulfilled' if t['status']=='success' else t['status']}'>{escape(t['status'])}</td><td class='ash'>{escape(t['ip_address'] or '')}</td><td class='ash'>{escape(t['created_at'][:19])}</td></tr>"
            for t in topups
        ),
    )
    redemptions_html = mini_table(
        ["UID", "Coins", "Status", "IP", "Date"],
        "".join(
            f"<tr><td style='font-family:monospace;'>{escape(r['uid_submitted'])}</td><td class='gold'>{r['coins_requested']}</td><td class='status-{'pending' if r['status']=='pending_approval' else r['status']}'>{escape(r['status'])}</td><td class='ash'>{escape(r['ip_address'] or '')}</td><td class='ash'>{escape(r['created_at'][:19])}</td></tr>"
            for r in redemptions
        ),
    )
    referrals_given_html = mini_table(
        ["Referred user", "Their IP", "Status", "Bonus", "Date"],
        "".join(
            f"<tr><td>{escape(r['referred_email'])}</td><td class='ash'>{escape(r['referred_ip'] or '—')}</td><td class='status-{'fulfilled' if r['status']=='completed' else 'pending'}'>{escape(r['status'])}</td><td class='gold'>{r['bonus_coins_awarded']}</td><td class='ash'>{escape(r['created_at'][:10])}</td></tr>"
            for r in referrals_given
        ),
        "Hasn't referred anyone yet.",
    )
    referred_by_html = mini_table(
        ["Referred by", "Their IP", "Status"],
        "".join(
            f"<tr><td>{escape(r['referrer_email'])}</td><td class='ash'>{escape(r['referrer_ip'] or '—')}</td><td class='status-{'fulfilled' if r['status']=='completed' else 'pending'}'>{escape(r['status'])}</td></tr>"
            for r in referrals_received
        ),
        "Wasn't referred by anyone.",
    )
    spins_html = mini_table(
        ["Prize", "IP", "Date"],
        "".join(
            f"<tr><td class=\"{'gold' if s['is_jackpot'] else ''}\">{s['prize_coins']}{' 🎉' if s['is_jackpot'] else ''}</td><td class='ash'>{escape(s['ip_address'] or '')}</td><td class='ash'>{escape(s['created_at'][:19])}</td></tr>"
            for s in spins
        ),
    )
    activity_html = mini_table(
        ["Action", "IP", "Device", "Date"],
        "".join(
            f"<tr><td>{escape(a['action'])}</td><td class='ash'>{escape(a['ip_address'] or '')}</td><td class='ash' style='max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{escape(a['user_agent'] or '')}</td><td class='ash'>{escape(a['created_at'][:19])}</td></tr>"
            for a in activity
        ),
    )

    return f"""{ADMIN_NAV}
<div class="container" style="padding:0 16px 40px;">
  <a href="/admin/users" class="ash" style="font-size:0.85rem;">&larr; Back to all users</a>
  <h1 style="margin:8px 0 20px;">{escape(user['name'])}</h1>

  <div class="grid grid-4" style="margin-bottom:20px;">
    {stat_card("Balance", user['coins_balance'], "gold")}
    {stat_card("On hold", user['coins_on_hold'])}
    {stat_card("Status", "Active" if user['is_active'] else "Banned", "text-white" if user['is_active'] else "text-white")}
    {stat_card("Referrals", "Allowed" if user['can_refer'] else "Restricted")}
  </div>

  <div class="card" style="margin-bottom:20px;">
    <p class="ash" style="font-size:0.85rem;">Email</p><p style="margin-bottom:10px;">{escape(user['email'])}</p>
    <p class="ash" style="font-size:0.85rem;">Referral code</p><p style="margin-bottom:10px;">{escape(user['referral_code'])}</p>
    <p class="ash" style="font-size:0.85rem;">Joined</p><p style="margin-bottom:10px;">{escape(user['created_at'][:19])}</p>
    <p class="ash" style="font-size:0.85rem;">Last login</p><p style="margin-bottom:10px;">{escape((user['last_login_at'] or '—')[:19] if user['last_login_at'] else '—')}</p>
    <p class="ash" style="font-size:0.85rem;">Last login IP</p><p style="margin-bottom:10px;">{escape(user['last_login_ip'] or '—')}</p>
    <p class="ash" style="font-size:0.85rem;">Last login device</p><p style="margin-bottom:14px;word-break:break-word;">{escape(user['last_login_user_agent'] or '—')}</p>
    {ban_form}{refer_form}
  </div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">Top-ups</h2>
  <div style="margin-bottom:20px;">{topups_html}</div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">Redemption requests</h2>
  <div style="margin-bottom:20px;">{redemptions_html}</div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">People they referred</h2>
  <div style="margin-bottom:20px;">{referrals_given_html}</div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">Who referred them</h2>
  <div style="margin-bottom:20px;">{referred_by_html}</div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">Spin history</h2>
  <div style="margin-bottom:20px;">{spins_html}</div>

  <h2 style="font-size:1rem;margin-bottom:8px;" class="orange">Activity log</h2>
  <div style="margin-bottom:20px;">{activity_html}</div>
</div>"""


def admin_topups_page(topups):
    rows = "".join(
        f"""<tr><td>{escape(t['email'])}</td><td class="gold">{t['coins']}</td><td>₦{t['amount_naira']:,}</td>
        <td class="ash">{escape(t['reference'])}</td><td class="status-{'fulfilled' if t['status']=='success' else t['status']}">{escape(t['status'])}</td>
        <td class="ash">{escape(t['ip_address'] or '')}</td><td class="ash">{escape(t['created_at'][:19])}</td></tr>"""
        for t in topups
    )
    body = history_page("Top-ups", rows, ["User", "Coins", "Amount", "Reference", "Status", "IP", "Date"])
    return ADMIN_NAV + body


def admin_redemptions_page(requests, csrf):
    rows = "".join(
        f"""<tr><td>{escape(r['email'])}</td><td style="font-family:monospace;">{escape(r['uid_submitted'])}</td>
        <td class="gold" style="font-weight:700;">{r['coins_requested']}</td>
        <td class="status-{'pending' if r['status']=='pending_approval' else r['status']}">{escape(r['status'])}</td>
        <td class="ash">{escape(r['ip_address'] or '')}</td>
        <td class="ash" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{escape(r['user_agent'] or '')}</td>
        <td class="ash">{escape(r['created_at'][:19])}</td>
        <td>{f'''<form method="POST" action="/admin/redemptions/{r['id']}/approve" style="display:inline;"><input type="hidden" name="csrf_token" value="{csrf}"/><button class="btn-blaze small" style="background:#16a34a;box-shadow:none;color:#fff;margin-right:4px;">Approve</button></form>
        <form method="POST" action="/admin/redemptions/{r['id']}/reject" style="display:inline;"><input type="hidden" name="csrf_token" value="{csrf}"/><button class="btn-blaze small" style="background:var(--ff-red);box-shadow:none;color:#fff;">Reject</button></form>''' if r['status']=='pending_approval' else ''}</td></tr>"""
        for r in requests
    )
    body = history_page("Redemption Requests", rows, ["User", "UID", "Coins", "Status", "IP", "Device", "Requested", "Actions"])
    return ADMIN_NAV + body


def admin_referrals_page(referrals):
    rows = "".join(
        f"""<tr><td>{escape(r['referrer_email'])}</td><td class="ash">{escape(r['referrer_ip'] or '—')}</td>
        <td>{escape(r['referred_email'])}</td><td class="ash">{escape(r['referred_ip'] or '—')}</td>
        <td class="status-{'fulfilled' if r['status']=='completed' else 'pending'}">{escape(r['status'])}</td>
        <td class="gold">{r['bonus_coins_awarded']}</td><td class="ash">{escape(r['created_at'][:10])}</td></tr>"""
        for r in referrals
    )
    body = history_page("Referrals", rows, ["Referrer", "Referrer IP", "Referred", "Referred IP", "Status", "Bonus coins", "Date"])
    return ADMIN_NAV + body


def admin_spins_page(spins):
    rows = "".join(
        f"""<tr><td>{escape(s['email'])}</td><td class="{'gold' if s['is_jackpot'] else ''}" style="font-weight:700;">{s['prize_coins']}{' 🎉' if s['is_jackpot'] else ''}</td>
        <td class="ash">{escape(s['ip_address'] or '')}</td><td class="ash">{escape(s['created_at'][:19])}</td></tr>"""
        for s in spins
    )
    body = history_page("Spin Logs", rows, ["User", "Prize", "IP", "Date"])
    return ADMIN_NAV + body


def admin_activity_page(logs):
    rows = "".join(
        f"""<tr><td>{escape(l['email'] or 'unknown')}</td><td>{escape(l['action'])}</td>
        <td class="ash">{escape(l['ip_address'] or '')}</td>
        <td class="ash" style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{escape(l['user_agent'] or '')}</td>
        <td class="ash">{escape(l['created_at'][:19])}</td></tr>"""
        for l in logs
    )
    body = history_page("Activity Log", rows, ["User", "Action", "IP", "Device", "Date"])
    return ADMIN_NAV + body
