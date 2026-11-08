"""菜园子 ordering backend: takes orders from the ordering page, confirms payments with the
payment provider, notifies the restaurant, and gives staff a transactions back office."""
import csv
import hmac
import io
import logging
import os
import secrets
import threading
import time
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, Response, abort, g, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)

import notify
import orders as om
import payments
import store

HERE = os.path.dirname(os.path.abspath(__file__))
KITCHEN = ["new", "preparing", "ready", "completed", "cancelled"]
PAY_LABEL = {"paynow": "PayNow", "card": "Card", "wallet": "Apple/Google Pay", "grab": "GrabPay", "cash": "Cash/NETS"}
STATUS_LABEL = {"pending": "Awaiting payment", "paid": "Paid", "failed": "Failed", "refunded": "Refunded",
                "unpaid_cash": "Pay at counter"}


def load_env(path):
    """Minimal .env reader (KEY=value lines) so no extra package is needed."""
    if os.path.exists(path):
        for line in open(path, encoding="utf8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def create_app(overrides=None):
    load_env(os.path.join(HERE, ".env"))
    cfg = {k: os.environ.get(k, "") for k in [
        "SECRET_KEY", "STAFF_PASSWORD", "DATABASE", "PUBLIC_URL", "PAYMENT_PROVIDER", "HITPAY_API_KEY", "HITPAY_SALT",
        "HITPAY_SANDBOX", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "ORDER_EMAIL_TO", "IGNORE_HOURS"]}
    cfg.update(overrides or {})
    cfg["PAYMENT_PROVIDER"] = cfg["PAYMENT_PROVIDER"] or "demo"
    if not cfg["SECRET_KEY"] or not cfg["STAFF_PASSWORD"]:
        raise RuntimeError("Set SECRET_KEY and STAFF_PASSWORD in backend/.env (see .env.example)")

    app = Flask(__name__, static_folder=None)
    app.config.update(SECRET_KEY=cfg["SECRET_KEY"], SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    db = store.connect(cfg["DATABASE"] or os.path.join(HERE, "orders.db"))
    provider = payments.get_provider(cfg)
    clock = cfg.get("CLOCK") or store.now_sgt          # tests can pass a fake clock
    failed_logins = {}
    lock = threading.Lock()                             # one shared SQLite connection: serialise requests

    @app.before_request
    def _lock():
        lock.acquire()
        g.locked = True

    @app.teardown_request
    def _unlock(exc):
        if g.pop("locked", False):
            if exc:
                db.rollback()
            lock.release()

    app.jinja_env.globals.update(PAY_LABEL=PAY_LABEL, STATUS_LABEL=STATUS_LABEL, KITCHEN=KITCHEN, provider=provider.name)

    def public_url(path):
        return (cfg["PUBLIC_URL"].rstrip("/") or request.host_url.rstrip("/")) + path

    # ---------- marking payments ----------
    def mark_paid(order_id, amount, ref, source):
        o = store.get_order(db, order_id)
        if not o:
            return False
        if o["pay_status"] == "paid":
            return True                                      # webhooks can arrive twice
        if abs(amount - o["total"]) > 0.005:
            store.add_event(db, order_id, "note", amount, f"{source}: amount {amount:.2f} does not match total {o['total']:.2f}, not marked paid")
            db.commit()
            return False
        db.execute("UPDATE orders SET pay_status='paid', paid_at=?, provider_ref=COALESCE(?, provider_ref) WHERE id=?",
                   (clock().isoformat(timespec="seconds"), ref, order_id))
        store.add_event(db, order_id, "paid", amount, f"{source} ref {ref}")
        db.commit()
        notify.send(cfg, store.get_order(db, order_id))
        return True

    # ---------- customer side ----------
    @app.get("/")
    def home():
        return send_from_directory(os.path.join(HERE, "static"), "index.html")

    @app.get("/<any(img, css, js):folder>/<path:name>")
    def static_file(folder, name):
        return send_from_directory(os.path.join(HERE, "static", folder), name, max_age=86400 if folder == "img" else 300)

    @app.get("/api/menu")
    def api_menu():
        return jsonify(items=om.MENU, hours=om.HOURS, open=bool(cfg.get("IGNORE_HOURS")) or om.is_open(clock()))

    @app.post("/api/orders")
    def api_create_order():
        data = request.get_json(silent=True) or {}
        now = clock()
        try:
            if not cfg.get("IGNORE_HOURS") and not om.is_open(now):
                raise om.OrderError("Online ordering is closed. We take orders 11:30am–2:30pm and 5:30pm–9:30pm.")
            member = bool(data.get("member"))
            lines, totals = om.price_order(data.get("items"), data.get("type"), member)
            cust = om.clean_customer(data)
        except om.OrderError as e:
            return jsonify(error=str(e)), 400
        oid, token = store.next_order_id(db, now), secrets.token_urlsafe(16)
        cash = cust["pay_method"] == "cash"
        row = dict(id=oid, token=token, created_at=now.isoformat(timespec="seconds"), order_type=data["type"],
                   member_price=int(member), pay_status="unpaid_cash" if cash else "pending",
                   provider="none" if cash else provider.name, **cust, **totals)
        db.execute(f"INSERT INTO orders({','.join(row)}) VALUES ({','.join('?' * len(row))})", list(row.values()))
        db.executemany("INSERT INTO order_items(order_id,item_id,name,option,qty,unit) VALUES (?,?,?,?,?,?)",
                       [(oid, l["item_id"], l["name"], l["option"], l["qty"], l["unit"]) for l in lines])
        store.add_event(db, oid, "created", totals["total"], f"{PAY_LABEL[cust['pay_method']]} via {row['provider']}")
        db.commit()
        status_url = public_url(f"/order/{oid}?t={token}")
        if cash:
            notify.send(cfg, store.get_order(db, oid))
            return jsonify(order_id=oid, total=totals["total"], status_url=status_url, pay_url=None)
        try:
            res = provider.create(row, {"return": status_url, "webhook": public_url(f"/webhooks/{provider.name}"),
                                        "demo_pay": public_url(f"/pay/demo/{oid}?t={token}")})
        except payments.PaymentError as e:
            logging.exception("payment create failed")
            db.execute("UPDATE orders SET pay_status='failed' WHERE id=?", (oid,))
            store.add_event(db, oid, "failed", None, str(e))
            db.commit()
            return jsonify(error="Payment could not be started. Please try again or pay at the counter."), 502
        db.execute("UPDATE orders SET provider_ref=? WHERE id=?", (res["ref"], oid))
        db.commit()
        return jsonify(order_id=oid, total=totals["total"], status_url=status_url, pay_url=res["pay_url"])

    def customer_order(oid):
        o = store.get_order(db, oid)
        if not o or not hmac.compare_digest(o["token"], request.args.get("t", "")):
            abort(404)
        return o

    @app.get("/order/<oid>")
    def order_status(oid):
        return render_template("order_status.html", o=customer_order(oid))

    @app.get("/api/orders/<oid>")
    def api_order_status(oid):
        o = customer_order(oid)
        return jsonify(pay_status=o["pay_status"], kitchen_status=o["kitchen_status"])

    @app.route("/pay/demo/<oid>", methods=["GET", "POST"])
    def demo_pay(oid):
        if provider.name != "demo":
            abort(404)
        o = customer_order(oid)
        if request.method == "POST":
            mark_paid(oid, o["total"], o["provider_ref"], "demo")
            return redirect(f"/order/{oid}?t={o['token']}")
        return render_template("demo_pay.html", o=o)

    @app.post("/webhooks/<name>")
    def webhook(name):
        if name != provider.name or name == "demo":
            abort(404)
        try:
            raw = request.get_data(cache=True) if name == "stripe" else b""   # Stripe signs the exact raw body
            oid, outcome, amount, ref = provider.parse_webhook(request.form, raw, request.headers)
        except payments.PaymentError as e:
            logging.warning("rejected webhook: %s", e)
            return "bad signature", 400
        if not oid or not store.get_order(db, oid):
            return "unknown order", 200
        if outcome == "paid":
            mark_paid(oid, amount, ref, name)
        elif outcome == "failed":
            db.execute("UPDATE orders SET pay_status='failed' WHERE id=? AND pay_status='pending'", (oid,))
            store.add_event(db, oid, "failed", amount, f"{name} ref {ref}")
            db.commit()
        return "ok", 200

    # ---------- staff back office ----------
    def staff_only(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if not session.get("staff"):
                return redirect(url_for("staff_login", next=request.full_path))
            if request.method == "POST" and not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "")):
                abort(400)
            return f(*a, **kw)
        return wrapper

    @app.route("/staff/login", methods=["GET", "POST"])
    def staff_login():
        err, ip = None, request.remote_addr
        if request.method == "POST":
            recent = [t for t in failed_logins.get(ip, []) if time.time() - t < 600]
            if len(recent) >= 5:
                err = "Too many attempts. Please wait 10 minutes."
            elif hmac.compare_digest(request.form.get("password", "").encode(), cfg["STAFF_PASSWORD"].encode()):
                session.clear(); session.permanent = True
                session.update(staff=True, csrf=secrets.token_urlsafe(16))
                nxt = request.args.get("next", "")
                return redirect(nxt if nxt.startswith("/staff") else url_for("transactions"))
            else:
                failed_logins[ip] = recent + [time.time()]
                err = "Wrong password."
        return render_template("login.html", err=err)

    @app.get("/staff/logout")
    def staff_logout():
        session.clear()
        return redirect(url_for("staff_login"))

    def filters():
        today = clock().date().isoformat()
        f = {k: request.args.get(k, "").strip() for k in ["from", "to", "status", "method", "q"]}
        for k in ("from", "to"):
            try:
                date.fromisoformat(f[k])
            except ValueError:
                f[k] = today
        if f["from"] > f["to"]:
            f["from"], f["to"] = f["to"], f["from"]
        return f

    def summarise(rows):
        paid = [r for r in rows if r["pay_status"] == "paid"]
        by_method = {}
        for r in paid:
            m = by_method.setdefault(r["pay_method"], {"count": 0, "total": 0.0})
            m["count"] += 1; m["total"] += r["total"]
        sum_ = lambda st: round(sum(r["total"] for r in rows if r["pay_status"] == st), 2)
        return {"orders": len(rows), "paid_count": len(paid), "paid_total": round(sum(r["total"] for r in paid), 2),
                "gst": round(sum(r["gst"] for r in paid), 2), "service": round(sum(r["service"] for r in paid), 2),
                "pending": sum_("pending"), "cash_due": sum_("unpaid_cash"), "refunded": sum_("refunded"),
                "failed": sum_("failed"), "by_method": by_method}

    @app.get("/staff")
    @staff_only
    def transactions():
        f = filters()
        rows = store.search_orders(db, f["from"], f["to"], f["status"] or None, f["method"] or None, f["q"] or None)
        t = clock().date()
        d = {"today": t, "yday": t - timedelta(days=1), "week": t - timedelta(days=6), "month": t.replace(day=1)}
        return render_template("transactions.html", rows=rows, f=f, s=summarise(rows), d=d, csrf=session["csrf"])

    @app.get("/staff/export.csv")
    @staff_only
    def export_csv():
        f = filters()
        rows = store.search_orders(db, f["from"], f["to"], f["status"] or None, f["method"] or None, f["q"] or None)
        buf = io.StringIO()
        cols = ["id", "created_at", "order_type", "customer_name", "phone", "table_no", "pay_method", "pay_status",
                "provider", "provider_ref", "paid_at", "subtotal", "service", "delivery_fee", "gst", "total", "kitchen_status"]
        w = csv.writer(buf); w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
        return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=transactions_{f['from']}_to_{f['to']}.csv"})

    @app.get("/staff/order/<oid>")
    @staff_only
    def staff_order(oid):
        o = store.get_order(db, oid) or abort(404)
        return render_template("order_detail.html", o=o, csrf=session["csrf"])

    @app.post("/staff/order/<oid>/<action>")
    @staff_only
    def staff_action(oid, action):
        o = store.get_order(db, oid) or abort(404)
        note = request.form.get("note", "").strip()[:200]
        if action == "kitchen" and request.form.get("status") in KITCHEN:
            db.execute("UPDATE orders SET kitchen_status=? WHERE id=?", (request.form["status"], oid))
            store.add_event(db, oid, "note", None, f"Kitchen status → {request.form['status']}")
        elif action == "cash" and o["pay_status"] == "unpaid_cash":
            db.execute("UPDATE orders SET pay_status='paid', paid_at=? WHERE id=?", (clock().isoformat(timespec="seconds"), oid))
            store.add_event(db, oid, "cash_received", o["total"], note or "Collected at counter")
        elif action == "refund" and o["pay_status"] == "paid":
            db.execute("UPDATE orders SET pay_status='refunded' WHERE id=?", (oid,))
            store.add_event(db, oid, "refunded", o["total"], note or "Refunded (record only – issue the refund in the provider dashboard)")
        elif action == "note" and note:
            store.add_event(db, oid, "note", None, note)
        else:
            abort(400)
        db.commit()
        return redirect(url_for("staff_order", oid=oid))

    app.db, app.cfg, app.mark_paid = db, cfg, mark_paid
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from waitress import serve        # production-grade server, works on Windows and Linux
    port = int(os.environ.get("PORT", 5050))
    logging.info("菜园子 backend on http://localhost:%s  (staff: /staff)", port)
    serve(create_app(), host="0.0.0.0", port=port)
