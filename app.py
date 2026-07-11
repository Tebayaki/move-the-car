import os
import time
import logging
from datetime import datetime, timezone, timedelta

import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOKEN = os.environ.get("TOKEN", "")
SENDKEY = os.environ.get("SENDKEY", "")
SERVERCHAN_URL = "https://sctapi.ftqq.com/{}.send"

# ── IP rate limiter ──────────────────────────────────────
_rate_limit_window = 30  # seconds
_rate_limit_store: dict[str, float] = {}


def _is_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    last = _rate_limit_store.get(ip)
    if last is not None and (now - last) < _rate_limit_window:
        return True
    _rate_limit_store[ip] = now
    return False


# ── Helper: extract real client IP ──────────────────────
def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


# ── Routes ───────────────────────────────────────────────
@app.route("/" + TOKEN)
def index():
    return render_template("index.html")


@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")


@app.route("/api/notify", methods=["POST"])
def notify():
    ip = _client_ip()

    # Rate limit check
    if _rate_limit_store.get(ip) and _is_rate_limited(ip):
        logging.warning("Rate limit hit for %s", ip)
        return jsonify({"ok": False, "error": "Too fast, please try again later."}), 429

    # Mark timestamp (re-entrant safe after check)
    _rate_limit_store[ip] = time.monotonic()

    if not SENDKEY:
        logging.error("SENDKEY is not configured")
        return jsonify({"ok": False, "error": "Server not configured properly."}), 500

    now = datetime.now(timezone(timedelta(hours=8)))  # CST
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    message = ""
    if request.is_json:
        message = (request.get_json(silent=True) or {}).get("message", "")
    else:
        message = request.form.get("message", "")
    if len(message) > 50:
        return jsonify({"ok": False, "error": "Message too long."}), 400
    title = "【挪车提醒】有人需要您挪车"
    content =f"""- 时间：{timestamp_str}
- IP：{ip}
{"> " + message if message else ""}
---
**请尽快前往挪车!**"""
    short_msg = message.replace("\n", " ")
    short = f"于{timestamp_str}收到来自{ip}的挪车通知{'：' + short_msg if short_msg else ''}"

    try:
        resp = requests.post(
            SERVERCHAN_URL.format(SENDKEY),
            data={"tags": "挪车通知", "title": title, "desp": content, "short": short},
            timeout=10,
        )
        result = resp.json()
        if result.get("code") == 0:
            logging.info("Push sent successfully for %s", ip)
            return jsonify({"ok": True})
        else:
            logging.error("ServerChan error: %s", result)
            return jsonify({"ok": False, "error": "Push service error."}), 502
    except requests.RequestException as e:
        logging.error("Request to ServerChan failed: %s", e)
        return jsonify({"ok": False, "error": "Push service unreachable."}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
