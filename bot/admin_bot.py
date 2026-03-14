"""
Admin Bot Service — port 5001
==============================
Simulates an admin visiting Level 2 pages with a privileged session cookie.

FIX: use `url` param in add_cookies (not `domain`) so cookie matches
     whatever host the page is actually served from.
"""
import os, asyncio, logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ADMIN_COOKIE_NAME  = os.environ.get("ADMIN_COOKIE_NAME",  "admin_session")
ADMIN_COOKIE_VALUE = os.environ.get("ADMIN_COOKIE",       "supersecretadmincookie_xsscart")
BOT_WAIT_MS        = int(os.environ.get("BOT_WAIT_MS",    "4000"))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "bot": "admin_bot"})


@app.route("/visit", methods=["POST"])
def visit():
    data = request.json or {}
    uuid = data.get("uuid")
    url  = data.get("url")
    if not uuid or not url:
        return jsonify({"error": "uuid and url required"}), 400

    app.logger.info(f"[bot] visiting: {url}")
    try:
        asyncio.run(_headless_visit(url))
        return jsonify({"status": "visited", "url": url})
    except Exception as e:
        app.logger.error(f"[bot] error: {e}")
        return jsonify({"status": "error", "detail": str(e)}), 500


async def _headless_visit(url: str):
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = await browser.new_context()

        # ✅ FIX: use `url` not `domain` — Playwright extracts the correct
        #         domain from the URL automatically. This works for both
        #         localhost and Docker (app:5000) environments.
        await ctx.add_cookies([{
            "name":  ADMIN_COOKIE_NAME,
            "value": ADMIN_COOKIE_VALUE,
            "url":   url,          # <-- was: "domain": APP_HOST (wrong)
            "path":  "/",
        }])

        page = await ctx.new_page()

        try:
            await page.goto(url, timeout=12_000, wait_until="domcontentloaded")
        except Exception as e:
            app.logger.warning(f"[bot] goto warning: {e}")

        # Wait for XSS to execute and exfiltrate
        await page.wait_for_timeout(BOT_WAIT_MS)
        await browser.close()
        app.logger.info(f"[bot] done")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
