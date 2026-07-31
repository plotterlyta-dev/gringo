import os
import json
import urllib.request
import urllib.error

PAYSTACK_API = "https://api.paystack.co"


class PaymentProvider:
    """Abstract interface. Both the dev simulator and the real Paystack
    provider implement this same shape, so the rest of the app (wallet
    crediting, referral logic) doesn't care which one is active."""

    def initialize_payment(self, *, coins, amount_naira, user_email, callback_url, reference):
        raise NotImplementedError

    def verify_payment(self, reference):
        raise NotImplementedError


class DevelopmentPaymentProvider(PaymentProvider):
    """No real money moves here. Used automatically whenever
    PAYSTACK_SECRET_KEY isn't set, so local development never needs real
    payment credentials."""

    def initialize_payment(self, *, coins, amount_naira, user_email, callback_url, reference):
        return {"reference": reference, "authorization_url": None, "status": "success"}  # simulated: always succeeds

    def verify_payment(self, reference):
        return {"status": "success", "amount_kobo": None}


class PaystackPaymentProvider(PaymentProvider):
    """Real Paystack integration using the Standard Checkout (redirect)
    flow — the user is sent to Paystack's own hosted payment page rather
    than us embedding card fields ourselves, which keeps this app out of
    PCI-DSS scope and needs no frontend JS/SDK at all.

    Uses only Python's built-in urllib, no `requests` package needed.
    """

    def __init__(self, secret_key):
        self.secret_key = secret_key

    def _request(self, method, path, body=None):
        url = f"{PAYSTACK_API}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.secret_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8"))

    def initialize_payment(self, *, coins, amount_naira, user_email, callback_url, reference):
        result = self._request(
            "POST",
            "/transaction/initialize",
            {
                "email": user_email,
                "amount": amount_naira * 100,  # Paystack expects kobo
                "reference": reference,
                "callback_url": callback_url,
            },
        )
        if not result.get("status"):
            return {"reference": reference, "authorization_url": None, "status": "failed", "error": result.get("message")}
        return {
            "reference": reference,
            "authorization_url": result["data"]["authorization_url"],
            "status": "pending",
        }

    def verify_payment(self, reference):
        # Always re-verify server-side against Paystack's own API — never
        # trust a client-side redirect or webhook payload's status/amount
        # alone, since either could theoretically be spoofed.
        result = self._request("GET", f"/transaction/verify/{reference}")
        data = result.get("data") or {}
        return {"status": data.get("status"), "amount_kobo": data.get("amount")}


def get_active_provider():
    secret = os.environ.get("PAYSTACK_SECRET_KEY", "").strip()
    if secret:
        return PaystackPaymentProvider(secret)
    return DevelopmentPaymentProvider()


def is_real_paystack_active():
    return bool(os.environ.get("PAYSTACK_SECRET_KEY", "").strip())


active_provider = get_active_provider()
