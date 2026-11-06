import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as backend  # noqa: E402
from store import SGT  # noqa: E402

LUNCH = datetime(2026, 11, 6, 12, 0, tzinfo=SGT)
NIGHT = datetime(2026, 11, 6, 23, 0, tzinfo=SGT)


def make(tmp_path, clock=LUNCH, **cfg):
    base = dict(SECRET_KEY="test", STAFF_PASSWORD="staff-pw", DATABASE=str(tmp_path / "t.db"), CLOCK=lambda: clock)
    base.update(cfg)
    a = backend.create_app(base)
    a.testing = True
    return a, a.test_client()


ORDER = {"items": [{"id": "hunan", "opt": 0, "qty": 2}, {"id": "duck", "opt": 1, "qty": 1}], "member": False,
         "type": "dine", "name": "Mervin Tan", "phone": "9123 4567", "table": "12", "payment": "paynow"}


def login(c):
    c.post("/staff/login", data={"password": "staff-pw"})
    with c.session_transaction() as s:
        return s["csrf"]


def test_menu(tmp_path):
    _, c = make(tmp_path)
    j = c.get("/api/menu").get_json()
    assert len(j["items"]) == 53 and j["open"] is True


def test_server_prices_ignore_browser(tmp_path):
    a, c = make(tmp_path)
    r = c.post("/api/orders", json={**ORDER, "items": [{"id": "hunan", "opt": 0, "qty": 2, "price": 0.01}]})
    # 2 × 20.9 = 41.80, +10% service 4.18, +9% GST 4.14 = 50.12
    assert r.status_code == 200 and r.get_json()["total"] == 50.12


def test_duck_whole_and_member_price(tmp_path):
    _, c = make(tmp_path)
    r = c.post("/api/orders", json={**ORDER, "member": True, "items": [{"id": "duck", "opt": 1, "qty": 1}], "type": "pickup"})
    assert r.get_json()["total"] == round(29.9 * 1.09, 2)


def test_closed_hours_rejected(tmp_path):
    _, c = make(tmp_path, clock=NIGHT)
    r = c.post("/api/orders", json=ORDER)
    assert r.status_code == 400 and "closed" in r.get_json()["error"]


@pytest.mark.parametrize("bad,msg", [({"phone": "1234"}, "mobile"), ({"table": ""}, "table"),
                                     ({"items": []}, "empty"), ({"items": [{"id": "nope", "qty": 1}]}, "menu"),
                                     ({"type": "delivery", "address": "x", "payment": "cash"}, "Cash")])
def test_validation(tmp_path, bad, msg):
    _, c = make(tmp_path)
    r = c.post("/api/orders", json={**ORDER, **bad})
    assert r.status_code == 400 and msg in r.get_json()["error"]


def test_demo_payment_flow_and_transactions(tmp_path):
    a, c = make(tmp_path)
    j = c.post("/api/orders", json=ORDER).get_json()
    oid = j["order_id"]
    assert oid == "CYZ-20261106-0001" and "/pay/demo/" in j["pay_url"]
    # staff see it as awaiting payment
    csrf = login(c)
    page = c.get("/staff").get_data(as_text=True)
    assert oid in page and "Awaiting payment" in page
    # customer pays on the demo page
    path = j["pay_url"].split("localhost", 1)[1]
    assert c.post(path).status_code == 302
    o = c.get(f"/staff/order/{oid}").get_data(as_text=True)
    assert "Paid" in o and "demo ref demo_" + oid in o
    page = c.get("/staff").get_data(as_text=True)
    assert "$89.45" in page       # paid takings: 2×20.90 + 32.80 = 74.60, +7.46 service, +7.39 GST
    # wrong status page token is hidden
    assert c.get(f"/order/{oid}?t=wrong").status_code == 404
    # refund + note + kitchen status are recorded in history
    c.post(f"/staff/order/{oid}/kitchen", data={"csrf": csrf, "status": "ready"})
    c.post(f"/staff/order/{oid}/refund", data={"csrf": csrf, "note": "Customer left"})
    o = c.get(f"/staff/order/{oid}").get_data(as_text=True)
    assert "Refunded" in o and "Customer left" in o and "Kitchen status → ready" in o
    # actions need the CSRF token
    assert c.post(f"/staff/order/{oid}/note", data={"note": "x"}).status_code == 400


def test_cash_order_and_collect(tmp_path):
    _, c = make(tmp_path)
    oid = c.post("/api/orders", json={**ORDER, "payment": "cash"}).get_json()["order_id"]
    csrf = login(c)
    assert "Cash to collect" in c.get("/staff?status=unpaid_cash").get_data(as_text=True)
    c.post(f"/staff/order/{oid}/cash", data={"csrf": csrf, "note": "NETS"})
    o = c.get(f"/staff/order/{oid}").get_data(as_text=True)
    assert "cash received" in o and "NETS" in o


def test_filters_search_and_csv(tmp_path):
    _, c = make(tmp_path)
    c.post("/api/orders", json=ORDER)
    c.post("/api/orders", json={**ORDER, "name": "Ah Huat", "payment": "cash"})
    login(c)
    assert "Ah Huat" in c.get("/staff?q=Huat").get_data(as_text=True)
    assert "Mervin" not in c.get("/staff?q=Huat").get_data(as_text=True)
    assert "No transactions" in c.get("/staff?from=2026-01-01&to=2026-01-02").get_data(as_text=True)
    r = c.get("/staff/export.csv?from=2026-11-06&to=2026-11-06")
    rows = r.get_data(as_text=True).strip().splitlines()
    assert r.mimetype == "text/csv" and len(rows) == 3 and rows[0].lstrip("﻿").startswith("id,created_at")


def test_staff_pages_need_login(tmp_path):
    _, c = make(tmp_path)
    assert c.get("/staff").status_code == 302
    assert c.get("/staff/export.csv").status_code == 302
    assert "Wrong password" in c.post("/staff/login", data={"password": "nope"}).get_data(as_text=True)


def test_login_lockout(tmp_path):
    _, c = make(tmp_path)
    for _ in range(5):
        c.post("/staff/login", data={"password": "nope"})
    assert "Too many attempts" in c.post("/staff/login", data={"password": "staff-pw"}).get_data(as_text=True)


def hitpay_app(tmp_path, monkeypatch):
    class R:
        status_code = 201
        def json(self): return {"id": "hp_req_1", "url": "https://sandbox.hit-pay.com/pay/hp_req_1"}
    sent = {}
    monkeypatch.setattr("payments.requests.post", lambda url, **kw: sent.update(url=url, **kw) or R())
    a, c = make(tmp_path, PAYMENT_PROVIDER="hitpay", HITPAY_API_KEY="k", HITPAY_SALT="salt", PUBLIC_URL="https://shop.example")
    return a, c, sent


def hitpay_sig(fields, salt="salt"):
    msg = "".join(f"{k}{fields[k]}" for k in sorted(fields))
    return hmac.new(salt.encode(), msg.encode(), hashlib.sha256).hexdigest()


def test_hitpay_create_and_webhook(tmp_path, monkeypatch):
    a, c, sent = hitpay_app(tmp_path, monkeypatch)
    j = c.post("/api/orders", json=ORDER).get_json()
    assert j["pay_url"].startswith("https://sandbox.hit-pay.com/") and "sandbox" in sent["url"]
    data = dict(sent["data"])
    assert data["amount"] == "89.45" and data["webhook"] == "https://shop.example/webhooks/hitpay"
    fields = {"payment_id": "pay_9", "payment_request_id": "hp_req_1", "amount": "89.45", "currency": "SGD",
              "status": "completed", "reference_number": j["order_id"]}
    assert c.post("/webhooks/hitpay", data={**fields, "hmac": "forged"}).status_code == 400
    assert c.post("/webhooks/hitpay", data={**fields, "hmac": hitpay_sig(fields)}).status_code == 200
    assert tuple(a.db.execute("SELECT pay_status, provider_ref FROM orders").fetchone()) == ("paid", "pay_9")
    # a webhook with the wrong amount never marks an order paid
    j2 = c.post("/api/orders", json=ORDER).get_json()
    f2 = {**fields, "reference_number": j2["order_id"], "amount": "1.00"}
    c.post("/webhooks/hitpay", data={**f2, "hmac": hitpay_sig(f2)})
    assert a.db.execute("SELECT pay_status FROM orders WHERE id=?", (j2["order_id"],)).fetchone()[0] == "pending"


def test_stripe_webhook(tmp_path, monkeypatch):
    class R:
        status_code = 200
        def json(self): return {"id": "cs_test_1", "url": "https://checkout.stripe.com/c/pay/cs_test_1"}
    monkeypatch.setattr("payments.requests.post", lambda url, **kw: R())
    a, c = make(tmp_path, PAYMENT_PROVIDER="stripe", STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_x")
    oid = c.post("/api/orders", json=ORDER).get_json()["order_id"]
    body = json.dumps({"type": "checkout.session.completed", "data": {"object": {
        "id": "cs_test_1", "client_reference_id": oid, "amount_total": 8945, "payment_status": "paid", "payment_intent": "pi_1"}}}).encode()
    t = str(int(time.time()))
    sig = hmac.new(b"whsec_x", f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    assert c.post("/webhooks/stripe", data=body, headers={"Stripe-Signature": f"t={t},v1=bad"}).status_code == 400
    assert c.post("/webhooks/stripe", data=body, headers={"Stripe-Signature": f"t={t},v1={sig}"}).status_code == 200
    assert tuple(a.db.execute("SELECT pay_status, provider_ref FROM orders").fetchone()) == ("paid", "pi_1")


def test_order_numbers_count_up_per_day(tmp_path):
    _, c = make(tmp_path)
    ids = [c.post("/api/orders", json=ORDER).get_json()["order_id"] for _ in range(3)]
    assert ids == ["CYZ-20261106-0001", "CYZ-20261106-0002", "CYZ-20261106-0003"]
