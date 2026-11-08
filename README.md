# 菜园子 Online Ordering (Mervin Restaurant)

- `app/index.html` – the ordering page (HTML). Works on desktop and mobile.
- `app/css/order.css` – its design (CSS).
- `app/js/order.js` – menu & prices (`const M` dishes, `const D` drinks), cart, ordering hours, checkout (JavaScript).
- `app/img/` – dish/drink photos and the logo.
- `test/record.py` – automated test that records a narrated video (needs `pip install playwright imageio-ffmpeg` and `python -m playwright install chromium`).
- `Mervin-Ordering-App-Test.mp4` – the recorded test run (26/26 checks passed).

## Run locally
    python -m http.server 8766 -d app
Then open http://localhost:8766

## Before going live
- Replace the placeholder PayNow QR with the restaurant's real one.
- Connect card / Apple Pay / Google Pay / GrabPay to a payment provider (e.g. Stripe, HitPay).
- Send orders to the restaurant (email, WhatsApp, or kitchen printer).
