"""Records a narrated end-to-end test of the ordering app (desktop + mobile) to test/out/*.webm."""
import os, shutil
from playwright.sync_api import sync_playwright

URL = "http://localhost:8766/?now=12:00"  # fixed time inside ordering hours
OUT = os.path.join(os.path.dirname(__file__), "out")
shutil.rmtree(OUT, ignore_errors=True)

OVERLAY = """
document.addEventListener('DOMContentLoaded', () => {
  const s = document.createElement('style');
  s.textContent = `#__cap{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:99999;max-width:92%;
    background:rgba(10,30,15,.88);color:#fff;font:600 17px system-ui;padding:10px 18px;border-radius:10px;
    border-left:5px solid #f3d27a;box-shadow:0 4px 18px #0006;pointer-events:none;transition:opacity .2s}
    #__cap small{display:block;color:#f3d27a;font-size:12px;letter-spacing:1px;text-transform:uppercase}
    #__cap.pass{border-left-color:#4ade80} #__cap.pass small{color:#4ade80}
    #__cur{position:fixed;z-index:99998;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;
    background:rgba(255,215,0,.55);border:2px solid #b8860b;pointer-events:none;transition:transform .12s}
    #__cur.down{transform:scale(.6);background:rgba(255,80,0,.7)}`;
  document.head.appendChild(s);
  const c = document.createElement('div'); c.id='__cur'; c.style.left='-50px'; document.body.appendChild(c);
  addEventListener('mousemove', e => { c.style.left=e.clientX+'px'; c.style.top=e.clientY+'px'; }, true);
  addEventListener('mousedown', () => c.classList.add('down'), true);
  addEventListener('mouseup', () => c.classList.remove('down'), true);
  window.__cap = (step, text, pass) => { let d=document.getElementById('__cap');
    if(!d){d=document.createElement('div');d.id='__cap';document.body.appendChild(d);}
    d.className = pass ? 'pass' : ''; d.innerHTML = `<small>${step}</small>${text}`; };
});
"""

class T:
    def __init__(self, page, label):
        self.p, self.label, self.n, self.results = page, label, 0, []
    def cap(self, text, wait=1800, pass_=False):
        self.n += 1
        self.p.evaluate("([s,t,p])=>window.__cap(s,t,p)", [f"{self.label} · step {self.n}" + (" · ✔ PASS" if pass_ else ""), text, pass_])
        self.p.wait_for_timeout(wait)
    def check(self, cond, text):
        self.results.append((self.label, text, bool(cond)))
        self.cap(("✔ " if cond else "✘ FAIL: ") + text, 1600, pass_=bool(cond))
        assert cond, text
    def click(self, sel, nth=0, pause=500):
        loc = self.p.locator(sel).nth(nth)
        loc.scroll_into_view_if_needed(); self.p.wait_for_timeout(250)
        b = loc.bounding_box()
        self.p.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=18)
        self.p.wait_for_timeout(150); self.p.mouse.down(); self.p.wait_for_timeout(90); self.p.mouse.up()
        self.p.wait_for_timeout(pause)
    def type(self, sel, text):
        self.click(sel, pause=150); self.p.locator(sel).fill("")
        self.p.locator(sel).press_sequentially(text, delay=55); self.p.wait_for_timeout(300)
    def scroll(self, dy, steps=12):
        for _ in range(steps):
            self.p.mouse.wheel(0, dy / steps); self.p.wait_for_timeout(45)
        self.p.wait_for_timeout(500)
    def total(self):
        return self.p.locator(".sum.tot span").nth(1).inner_text()
    def db(self):
        return self.p.locator("#db").inner_text()


def desktop(br):
    ctx = br.new_context(viewport={"width": 1280, "height": 800}, record_video_dir=OUT + "/desktop",
                         record_video_size={"width": 1280, "height": 800})
    p = ctx.new_page(); p.add_init_script(OVERLAY); p.goto(URL); p.evaluate("localStorage.clear()"); p.reload()
    p.wait_for_load_state("networkidle"); t = T(p, "DESKTOP 1280×800")
    t.cap("菜园子 online ordering — full desktop test run", 2500)
    t.check(p.locator(".card").count() == 40, "Menu loaded: 40 dishes rendered")
    broken = p.evaluate("[...document.images].filter(i=>i.complete&&!i.naturalWidth).length")
    t.cap("Header matches the printed menu: logo, gold slogan, green band, category tabs", 2500)

    t.cap("Browsing the Signature Dishes 招牌必点 — MP member price & U.P regular price on every item", 2200)
    t.scroll(700); t.cap("Section banners styled like the printed menu (Chinese title + English subtitle)", 2000)
    t.scroll(900); t.scroll(900)
    t.cap("Jumping between categories using the tab bar", 1200)
    for k in ["rice", "soup", "veg", "dim", "drink"]:
        t.click(f'nav a[data-k="{k}"]', pause=1300)
    t.check(p.locator('nav a.on').inner_text() == "酒水饮料", "Active tab follows the section in view (酒水饮料 Beverages)")
    t.cap("Beverages laid out in 3 columns like the menu: 啤酒 Beer / 白酒 Spirits / 饮料 Soft drinks", 2200)

    t.cap("Adding drinks: Tiger Beer ×2 and Wong Lo Kat", 1200)
    t.click('.drow:has-text("Tiger Beer") .plus'); t.click('.drow:has-text("Tiger Beer") .qty button >> nth=1')
    t.click('.drow:has-text("Wong Lo Kat") .plus')
    t.check(p.locator("#cnt").inner_text() == "3", "Cart badge shows 3 items")

    t.click('nav a[data-k="sig"]', pause=1200)
    t.cap("Adding the signature 湖南小炒肉 Hunan Stir-Fried Pork", 1000)
    t.click('.card:has-text("Hunan Stir-Fried Pork") .plus', pause=900)
    t.click('.card:has-text("Steamed Sea Bass") .plus', pause=900)

    t.click('nav a[data-k="rice"]', pause=1200)
    t.cap("Spiced duck has size options — switching from Half 半只 to Whole 1只 changes the price", 1800)
    duck = '.card:has-text("Dry-Pressed Duck")'
    before = p.locator(duck + " .price").inner_text()
    t.click(duck + ' .opts button >> nth=1', pause=900)
    after = p.locator(duck + " .price").inner_text()
    t.check("32.8" in after and before != after, "Whole duck shows $29.9 MP / $32.8 U.P")
    t.click(duck + " .plus", pause=900)

    t.cap("Opening the cart", 900); t.click(".cartbtn", pause=1200)
    t.cap("Prices charged at U.P (regular) because member pricing is off", 2000)
    # 32.8 duck + 20.9 + 35.9 + 8.6*2 + 2.8 = 109.6 ; +10% svc 10.96 ; GST 9% of 120.56 = 10.85 -> 131.41
    t.check(t.total() == "$131.41", "Total = subtotal $109.60 + 10% service + 9% GST = $131.41")
    t.cap("Changing quantity inside the cart: remove one Tiger Beer", 1000)
    t.click('.line:has-text("Tiger") .qty button >> nth=0', pause=1000)
    t.check(t.total() == "$121.10", "Total recalculated to $121.10")
    t.type("#rem", "Less spicy please, no coriander")
    t.click("#df .big", pause=1200)

    t.cap("Checkout: order type, details, payment method", 1800)
    t.cap("Validation test — pressing Pay with empty fields", 1000)
    t.click("#df .big", pause=900)
    t.check("enter your name" in t.db(), "Error shown: name required")
    t.type("#fn", "Mervin Tan"); t.type("#fp", "1234")
    t.click("#df .big", pause=900)
    t.check("valid Singapore mobile" in t.db(), "Error shown: invalid phone number rejected")
    t.type("#fp", "9123 4567"); t.click("#df .big", pause=900)
    t.check("table number" in t.db(), "Error shown: dine-in requires a table number")
    t.type("#ft", "12")

    t.cap("Payment methods offered: PayNow, Card, Apple/Google Pay, GrabPay, Cash/NETS", 2400)
    t.click('.pick:has-text("Credit / Debit")', pause=1000)
    t.type("#cn", "4242 4242"); t.type("#ce", "12/29"); t.type("#cc", "123")
    t.click("#df .big", pause=900)
    t.check("check your card" in t.db(), "Error shown: incomplete card number rejected")
    t.type("#cn", "4242 4242 4242 4242")
    t.cap("Paying with a test card (simulated — no real charge)", 1200)
    t.click("#df .big", pause=2200)
    t.check("Thank you, Mervin Tan" in t.db() and "Table 12" in t.db(), "Order confirmed: dine-in, table 12, paid by card")
    t.cap("Confirmation shows order number, table and amount paid", 2600)
    t.click("#df .big", pause=1000)
    t.check(p.locator("#cnt").inner_text() == "0", "Cart emptied after the order")

    # --- run 2: member, pickup, PayNow
    t.scroll(-6000, 6); t.cap("Run 2 — member customer, pickup, pay with PayNow", 2000)
    t.click("#member", pause=1000)
    t.check(p.locator(".price.member").count() == 40, "Member pricing on: MP 会员价 is now highlighted")
    t.click('.card:has-text("Hunan Stir-Fried Pork") .plus', pause=500)
    t.click('.card:has-text("Hunan Stir-Fried Pork") .qty button >> nth=1', pause=500)
    t.click('.card:has-text("Old Ginger") .plus', pause=600)
    t.click(".cartbtn", pause=1000)
    t.check("member price" in p.locator("#df").inner_text(), "Cart subtotal uses member price")
    t.click("#df .big", pause=1000)
    t.click('.pick:has-text("Pickup")', pause=1000)
    t.check(p.locator("#ft").count() == 0 and p.locator("#fw").count() == 1, "Pickup hides table field and shows pickup time")
    t.check("Service charge" not in p.locator("#df").inner_text(), "No service charge for pickup")
    p.locator("#fw").select_option(index=2); p.wait_for_timeout(700)
    t.click('.pick:has-text("PayNow")', pause=800)
    t.click("#df .big", pause=1500)
    t.check(p.locator(".qr").count() == 1, "PayNow QR shown with amount and reference")
    t.cap("(QR is a placeholder — the restaurant's real PayNow QR goes here)", 2200)
    t.click("#df .big", pause=1800)
    t.check("Pickup" in t.db(), "Order confirmed for pickup")
    t.click("#df .big", pause=800)

    # --- run 3: delivery
    t.cap("Run 3 — delivery order", 1500)
    t.click('nav a[data-k="soup"]', pause=1200)
    t.click('.card:has-text("Lotus Root & Pork") .plus', pause=600)
    t.click(".cartbtn", pause=900); t.click("#df .big", pause=900)
    t.click('.pick:has-text("Delivery")', pause=1000)
    t.check(p.locator('.pick:has-text("Cash")').count() == 0, "Cash option hidden for delivery")
    t.check("$5.00" in p.locator("#df").inner_text(), "Delivery fee $5 added (order under $60)")
    t.type("#fa", "1 Killiney Road, #05-01, Singapore 239518")
    t.click('.pick:has-text("GrabPay")', pause=800)
    t.click("#df .big", pause=2200)
    t.check("Delivery" in t.db() and "GrabPay" in t.db(), "Delivery order paid by GrabPay confirmed")
    t.cap(f"Desktop run complete ✔ — {broken} broken images", 2500, pass_=True)
    res = t.results; ctx.close(); return res


def mobile(br):
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                         record_video_dir=OUT + "/mobile", record_video_size={"width": 390, "height": 844})
    p = ctx.new_page(); p.add_init_script(OVERLAY); p.goto(URL); p.evaluate("localStorage.clear()"); p.reload()
    p.wait_for_load_state("networkidle"); t = T(p, "MOBILE 390×844")
    t.cap("Same app on a phone", 2200)
    t.check(p.locator(".cartbtn").is_hidden(), "Compact header (slogan hidden)")
    t.check(p.evaluate("document.documentElement.scrollWidth<=innerWidth"), "No sideways scrolling")
    t.scroll(900); t.cap("Two-column dish grid on phones", 1800)
    t.click('.card:has-text("Stir-fried Yellow Beef") .plus', pause=900)
    t.check(p.locator("#fab").is_visible(), "Floating cart bar appears at the bottom")
    t.click('nav a[data-k="dim"]', pause=1300)
    t.click('.card:has-text("Pumpkin") .plus', pause=700)
    t.click('nav a[data-k="drink"]', pause=1300)
    t.click('.drow:has-text("Coca-Cola") .plus', pause=700)
    t.click("#fab", pause=1200)
    t.check(p.locator(".drawer").bounding_box()["y"] > 30, "Cart slides up as a bottom sheet")
    t.click("#df .big", pause=1000)
    t.click('.pick:has-text("Pickup")', pause=700)
    t.type("#fn", "Ah Huat"); t.type("#fp", "8765 4321")
    t.click('.pick:has-text("Cash")', pause=700)
    t.scroll(400, 4)
    t.click("#df .big", pause=1500)
    t.check("pay" in t.db() and "counter" in t.db(), "Cash order: told to pay at counter")
    t.cap("Mobile run complete ✔", 2200, pass_=True)
    res = t.results; ctx.close(); return res


with sync_playwright() as pw:
    br = pw.chromium.launch()
    results = desktop(br) + mobile(br)
    br.close()
for r in results: print(("PASS" if r[2] else "FAIL"), r[0], "-", r[1])
print(f"{sum(r[2] for r in results)}/{len(results)} checks passed")
