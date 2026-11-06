"""Tell the restaurant about new orders: Telegram and/or e-mail if configured, always the server log."""
import logging
import smtplib
from email.message import EmailMessage

import requests

log = logging.getLogger("cyz.notify")
TYPE = {"dine": "Dine-in", "pickup": "Pickup", "delivery": "Delivery"}


def order_text(o):
    where = {"dine": f"Table {o['table_no']}", "pickup": f"Pickup {o['ready_time']}",
             "delivery": f"Deliver {o['ready_time']} to {o['address']}"}[o["order_type"]]
    pay = "UNPAID – collect cash/NETS at counter" if o["pay_status"] == "unpaid_cash" else f"PAID {o['pay_method']} ({o['provider_ref']})"
    lines = [f"🧾 New order {o['id']} – {TYPE[o['order_type']]}", where, f"{o['customer_name']} · {o['phone']}", ""]
    lines += [f"{i['qty']} × {i['name']}{' (' + i['option'] + ')' if i['option'] else ''}  ${i['unit'] * i['qty']:.2f}" for i in o["lines"]]
    if o.get("notes"):
        lines += ["", "Notes: " + o["notes"]]
    lines += ["", f"Total ${o['total']:.2f} – {pay}"]
    if o["member_price"]:
        lines.append("⚠ Member price used – please check membership")
    return "\n".join(lines)


def send(cfg, o):
    text = order_text(o)
    log.info("ORDER NOTIFICATION\n%s", text)
    sent = []
    if cfg.get("TELEGRAM_BOT_TOKEN") and cfg.get("TELEGRAM_CHAT_ID"):
        try:
            requests.post(f"https://api.telegram.org/bot{cfg['TELEGRAM_BOT_TOKEN']}/sendMessage",
                          json={"chat_id": cfg["TELEGRAM_CHAT_ID"], "text": text}, timeout=10).raise_for_status()
            sent.append("telegram")
        except Exception as e:  # a failed notification must never lose the order
            log.error("Telegram failed: %s", e)
    if cfg.get("SMTP_HOST") and cfg.get("ORDER_EMAIL_TO"):
        try:
            m = EmailMessage()
            m["Subject"], m["From"], m["To"] = f"New order {o['id']} – ${o['total']:.2f}", cfg.get("SMTP_FROM") or cfg.get("SMTP_USER"), cfg["ORDER_EMAIL_TO"]
            m.set_content(text)
            with smtplib.SMTP(cfg["SMTP_HOST"], int(cfg.get("SMTP_PORT") or 587), timeout=15) as s:
                s.starttls()
                if cfg.get("SMTP_USER"):
                    s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
                s.send_message(m)
            sent.append("email")
        except Exception as e:
            log.error("E-mail failed: %s", e)
    return sent
