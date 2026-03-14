"""
GET /webhook/bot-status  — returns Playwright availability (no longer a remote service)
"""
from flask import Blueprint, jsonify

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook/bot-status")
def bot_status():
    from app.bot import is_available
    ok = is_available()
    return jsonify({
        "online": ok,
        "mode":   "embedded" if ok else "unavailable",
        "note":   "Playwright runs inside Flask process" if ok
                  else "Run: pip install playwright && playwright install chromium"
    })
