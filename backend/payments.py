"""Payment providers. Each one creates a hosted payment page for an order and verifies the
provider's webhook, so an order is only marked paid when the provider itself says so.

PAYMENT_PROVIDER=demo   – no real money; a test page lets you mark the order paid (default)
PAYMENT_PROVIDER=hitpay – HitPay payment requests (Singapore: PayNow, cards, GrabPay, wallets)
PAYMENT_PROVIDER=stripe – Stripe Checkout

The HitPay and Stripe calls follow their public API docs. Run them in each provider's
sandbox / test mode before switching to live keys.
"""
import hashlib
import hmac
import time

import requests


class PaymentError(RuntimeError):
    pass


class Demo:
    name = "demo"

    def __init__(self, cfg):
        self.cfg = cfg

    def create(self, order, urls):
        return {"ref": "demo_" + order["id"], "pay_url": urls["demo_pay"]}


class HitPay:
    name = "hitpay"
    METHODS = {"paynow": ["paynow_online"], "card": ["card"], "wallet": ["card"], "grab": ["grabpay"]}

    def __init__(self, cfg):
        self.key, self.salt = cfg["HITPAY_API_KEY"], cfg["HITPAY_SALT"]
        self.base = "https://api.sandbox.hit-pay.com" if cfg.get("HITPAY_SANDBOX") != "0" else "https://api.hit-pay.com"
        if not self.key or not self.salt:
            raise PaymentError("HITPAY_API_KEY and HITPAY_SALT must be set")

    def create(self, order, urls):
        data = [("amount", f"{order['total']:.2f}"), ("currency", "SGD"), ("reference_number", order["id"]),
                ("redirect_url", urls["return"]), ("webhook", urls["webhook"]),
                ("name", order["customer_name"]), ("phone", order["phone"]), ("purpose", f"菜园子 order {order['id']}")]
        data += [("payment_methods[]", m) for m in self.METHODS.get(order["pay_method"], [])]
        r = requests.post(self.base + "/v1/payment-requests", data=data, timeout=15,
                          headers={"X-BUSINESS-API-KEY": self.key, "X-Requested-With": "XMLHttpRequest"})
        if r.status_code >= 300:
            raise PaymentError(f"HitPay error {r.status_code}: {r.text[:200]}")
        j = r.json()
        return {"ref": j["id"], "pay_url": j["url"]}

    def sign(self, fields):
        msg = "".join(f"{k}{fields[k]}" for k in sorted(fields) if k != "hmac")
        return hmac.new(self.salt.encode(), msg.encode(), hashlib.sha256).hexdigest()

    def parse_webhook(self, form, raw, headers):
        """Returns (order_id, outcome, amount, provider_ref) or raises PaymentError."""
        fields = dict(form)
        if not hmac.compare_digest(self.sign(fields), fields.get("hmac", "")):
            raise PaymentError("Bad HitPay signature")
        outcome = {"completed": "paid", "failed": "failed"}.get(fields.get("status"), "note")
        return fields.get("reference_number"), outcome, float(fields.get("amount") or 0), fields.get("payment_id")


class Stripe:
    name = "stripe"
    METHODS = {"paynow": ["paynow"], "card": ["card"], "wallet": ["card"], "grab": ["grabpay"]}

    def __init__(self, cfg):
        self.key, self.whsec = cfg["STRIPE_SECRET_KEY"], cfg["STRIPE_WEBHOOK_SECRET"]
        if not self.key or not self.whsec:
            raise PaymentError("STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET must be set")

    def create(self, order, urls):
        data = [("mode", "payment"), ("client_reference_id", order["id"]), ("metadata[order_id]", order["id"]),
                ("success_url", urls["return"]), ("cancel_url", urls["return"]),
                ("line_items[0][quantity]", "1"), ("line_items[0][price_data][currency]", "sgd"),
                ("line_items[0][price_data][unit_amount]", str(round(order["total"] * 100))),
                ("line_items[0][price_data][product_data][name]", f"菜园子 order {order['id']}")]
        data += [("payment_method_types[]", m) for m in self.METHODS.get(order["pay_method"], [])]
        r = requests.post("https://api.stripe.com/v1/checkout/sessions", data=data, auth=(self.key, ""), timeout=15)
        if r.status_code >= 300:
            raise PaymentError(f"Stripe error {r.status_code}: {r.text[:200]}")
        j = r.json()
        return {"ref": j["id"], "pay_url": j["url"]}

    def parse_webhook(self, form, raw, headers, tolerance=300):
        parts = dict(p.split("=", 1) for p in headers.get("Stripe-Signature", "").split(",") if "=" in p)
        t, sig = parts.get("t", ""), parts.get("v1", "")
        expected = hmac.new(self.whsec.encode(), f"{t}.".encode() + raw, hashlib.sha256).hexdigest()
        if not t.isdigit() or not hmac.compare_digest(expected, sig) or abs(time.time() - int(t)) > tolerance:
            raise PaymentError("Bad Stripe signature")
        import json
        ev = json.loads(raw)
        obj = ev.get("data", {}).get("object", {})
        oid = obj.get("client_reference_id") or obj.get("metadata", {}).get("order_id")
        amount = (obj.get("amount_total") or 0) / 100
        kind = ev.get("type")
        if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded") and obj.get("payment_status") == "paid":
            return oid, "paid", amount, obj.get("payment_intent") or obj.get("id")
        if kind in ("checkout.session.async_payment_failed", "checkout.session.expired"):
            return oid, "failed", amount, obj.get("id")
        return oid, "note", amount, obj.get("id")


PROVIDERS = {"demo": Demo, "hitpay": HitPay, "stripe": Stripe}


def get_provider(cfg):
    name = cfg.get("PAYMENT_PROVIDER", "demo")
    if name not in PROVIDERS:
        raise PaymentError(f"Unknown PAYMENT_PROVIDER {name!r}")
    return PROVIDERS[name](cfg)
