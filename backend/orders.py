"""Menu, ordering hours and price calculation. The server always recalculates prices;
whatever the browser sends as a price is ignored."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "menu.json"), encoding="utf8") as f:
    MENU = json.load(f)
BY_ID = {m["id"]: m for m in MENU}

# Singapore time, minutes after midnight (must match HOURS in static/index.html)
HOURS = [(690, 870), (1050, 1290)]          # 11:30–14:30, 17:30–21:30
PAY_METHODS = {"paynow", "card", "wallet", "grab", "cash"}
ORDER_TYPES = {"dine", "pickup", "delivery"}
SERVICE_RATE, GST_RATE = 0.10, 0.09
DELIVERY_FEE, FREE_DELIVERY_FROM = 5.0, 60.0
MAX_QTY = 50


class OrderError(ValueError):
    pass


def is_open(now):
    m = now.hour * 60 + now.minute
    return any(a <= m < b for a, b in HOURS)


def unit_price(item, opt, member):
    if item.get("opts"):
        if not (0 <= opt < len(item["opts"])):
            raise OrderError(f"Unknown option for {item['en']}")
        _, mp, up = item["opts"][opt]
        return (mp if member else up), item["opts"][opt][0]
    return (item["mp"] if member else item["up"]), None


def r2(x):
    return round(x + 1e-9, 2)


def price_order(lines, order_type, member):
    """lines: [{'id':..,'opt':0,'qty':2}] -> (priced lines, totals dict)."""
    if order_type not in ORDER_TYPES:
        raise OrderError("Unknown order type")
    priced = []
    for ln in lines or []:
        item = BY_ID.get(str(ln.get("id")))
        if not item:
            raise OrderError("An item in your cart is no longer on the menu")
        try:
            qty, opt = int(ln.get("qty", 0)), int(ln.get("opt", 0))
        except (TypeError, ValueError):
            raise OrderError("Invalid quantity")
        if not (1 <= qty <= MAX_QTY):
            raise OrderError("Invalid quantity")
        unit, opt_name = unit_price(item, opt, member)
        priced.append({"item_id": item["id"], "name": f"{item['zh']} {item['en']}", "option": opt_name, "qty": qty, "unit": unit})
    if not priced:
        raise OrderError("Your cart is empty")
    sub = r2(sum(p["unit"] * p["qty"] for p in priced))
    svc = r2(sub * SERVICE_RATE) if order_type == "dine" else 0.0
    dlv = (0.0 if sub >= FREE_DELIVERY_FROM else DELIVERY_FEE) if order_type == "delivery" else 0.0
    gst = r2((sub + svc + dlv) * GST_RATE)
    return priced, {"subtotal": sub, "service": svc, "delivery_fee": dlv, "gst": gst, "total": r2(sub + svc + dlv + gst)}


def clean_customer(data):
    name = str(data.get("name", "")).strip()[:80]
    phone = re.sub(r"\D", "", str(data.get("phone", "")))
    phone = phone[2:] if len(phone) == 10 and phone.startswith("65") else phone
    if not name:
        raise OrderError("Please enter your name")
    if not re.fullmatch(r"[689]\d{7}", phone):
        raise OrderError("Please enter a valid Singapore mobile number")
    t = data.get("type")
    table = str(data.get("table", "")).strip()[:10]
    address = str(data.get("address", "")).strip()[:300]
    if t == "dine" and not table:
        raise OrderError("Please enter your table number")
    if t == "delivery" and not address:
        raise OrderError("Please enter your delivery address")
    method = data.get("payment")
    if method not in PAY_METHODS:
        raise OrderError("Please choose a payment method")
    if method == "cash" and t == "delivery":
        raise OrderError("Cash is not available for delivery")
    return {"customer_name": name, "phone": phone, "table_no": table or None, "address": address or None,
            "ready_time": str(data.get("time", "asap"))[:10], "notes": str(data.get("notes", "")).strip()[:300] or None,
            "pay_method": method}
