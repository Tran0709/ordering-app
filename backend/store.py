"""SQLite storage for orders, their items and every payment event (the transaction log)."""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

SGT = timezone(timedelta(hours=8))

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id            TEXT PRIMARY KEY,          -- e.g. CYZ-20261106-0007
    token         TEXT NOT NULL,             -- secret for the customer's status page
    created_at    TEXT NOT NULL,             -- ISO time, Singapore
    order_type    TEXT NOT NULL,             -- dine | pickup | delivery
    customer_name TEXT NOT NULL,
    phone         TEXT NOT NULL,
    table_no      TEXT,
    address       TEXT,
    ready_time    TEXT,
    notes         TEXT,
    member_price  INTEGER NOT NULL DEFAULT 0,
    subtotal      REAL NOT NULL,
    service       REAL NOT NULL,
    delivery_fee  REAL NOT NULL,
    gst           REAL NOT NULL,
    total         REAL NOT NULL,
    pay_method    TEXT NOT NULL,             -- paynow | card | wallet | grab | cash
    pay_status    TEXT NOT NULL,             -- pending | paid | failed | refunded | unpaid_cash
    provider      TEXT,                      -- demo | hitpay | stripe | none
    provider_ref  TEXT,                      -- payment id at the provider
    paid_at       TEXT,
    kitchen_status TEXT NOT NULL DEFAULT 'new'  -- new | preparing | ready | completed | cancelled
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL REFERENCES orders(id),
    item_id  TEXT NOT NULL,
    name     TEXT NOT NULL,
    option   TEXT,
    qty      INTEGER NOT NULL,
    unit     REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS payment_events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id  TEXT NOT NULL REFERENCES orders(id),
    at        TEXT NOT NULL,
    kind      TEXT NOT NULL,                 -- created | paid | failed | refunded | cash_received | note
    amount    REAL,
    detail    TEXT                           -- JSON or free text
);
CREATE INDEX IF NOT EXISTS orders_created ON orders(created_at);
"""


def now_sgt():
    return datetime.now(SGT)


def connect(path):
    db = sqlite3.connect(path, detect_types=0, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    return db


def next_order_id(db, day):
    prefix = f"CYZ-{day:%Y%m%d}-"
    row = db.execute("SELECT id FROM orders WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (prefix + "%",)).fetchone()
    n = int(row["id"].rsplit("-", 1)[1]) + 1 if row else 1
    return f"{prefix}{n:04d}"


def add_event(db, order_id, kind, amount=None, detail=None):
    if detail is not None and not isinstance(detail, str):
        detail = json.dumps(detail, ensure_ascii=False)
    db.execute("INSERT INTO payment_events(order_id, at, kind, amount, detail) VALUES (?,?,?,?,?)",
               (order_id, now_sgt().isoformat(timespec="seconds"), kind, amount, detail))


def get_order(db, order_id):
    o = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not o:
        return None
    o = dict(o)
    o["lines"] = [dict(r) for r in db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))]
    o["events"] = [dict(r) for r in db.execute("SELECT * FROM payment_events WHERE order_id=? ORDER BY id", (order_id,))]
    return o


def search_orders(db, date_from, date_to, pay_status=None, pay_method=None, q=None):
    """Orders created between two dates (inclusive, YYYY-MM-DD, Singapore time), newest first."""
    sql = "SELECT * FROM orders WHERE substr(created_at,1,10) BETWEEN ? AND ?"
    args = [date_from, date_to]
    if pay_status:
        sql += " AND pay_status=?"; args.append(pay_status)
    if pay_method:
        sql += " AND pay_method=?"; args.append(pay_method)
    if q:
        sql += " AND (id LIKE ? OR customer_name LIKE ? OR phone LIKE ? OR provider_ref LIKE ?)"
        args += [f"%{q}%"] * 4
    return [dict(r) for r in db.execute(sql + " ORDER BY created_at DESC", args)]
