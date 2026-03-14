"""
Embedded admin bot — runs directly inside the Flask process.

COOKIE FIX: navigate first, set cookie, reload.
"""
import threading, logging, os
from urllib.parse import urlparse

log = logging.getLogger("admin_bot")

ADMIN_COOKIE_NAME  = os.environ.get("ADMIN_COOKIE_NAME",  "admin_session")
ADMIN_COOKIE_VALUE = os.environ.get("ADMIN_COOKIE",       "supersecretadmincookie_xsscart")
BOT_WAIT_MS        = int(os.environ.get("BOT_WAIT_MS",    "5000"))


def _do_visit(url: str):
    try:
        from playwright.sync_api import sync_playwright

        parsed   = urlparse(url)
        hostname = parsed.hostname  # "localhost" or "127.0.0.1"

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage",
                      "--disable-gpu", "--disable-setuid-sandbox"]
            )
            ctx  = browser.new_context()
            page = ctx.new_page()

            # ── STEP 1: visit page first to establish domain context ──────
            log.info(f"[bot] step 1 — first visit: {url}")
            try:
                page.goto(url, timeout=12_000, wait_until="domcontentloaded")
            except Exception as e:
                log.warning(f"[bot] goto (ok to warn): {e}")

            # ── STEP 2: NOW set the admin cookie on the known domain ──────
            log.info(f"[bot] step 2 — setting cookie for domain '{hostname}'")
            ctx.add_cookies([{
                "name":   ADMIN_COOKIE_NAME,
                "value":  ADMIN_COOKIE_VALUE,
                "domain": hostname,
                "path":   "/",
            }])

            # ── STEP 3: reload so cookie is sent with the request ─────────
            log.info(f"[bot] step 3 — reload with cookie attached")
            try:
                page.reload(timeout=12_000, wait_until="domcontentloaded")
            except Exception as e:
                log.warning(f"[bot] reload (ok to warn): {e}")

            # Verify cookie is actually visible to JavaScript
            try:
                doc_cookie = page.evaluate("document.cookie")
                log.info(f"[bot] document.cookie = '{doc_cookie[:80]}'")
            except Exception as e:
                log.warning(f"[bot] evaluate: {e}")

            # ── STEP 4: wait for XSS payload to fire ─────────────────────
            log.info(f"[bot] step 4 — waiting {BOT_WAIT_MS}ms for XSS...")
            page.wait_for_timeout(BOT_WAIT_MS)

            browser.close()
            log.info(f"[bot] done")

    except Exception as e:
        log.error(f"[bot] visit failed: {e}")


def dispatch(url: str):
    """Non-blocking: fire bot in background thread."""
    log.info(f"[bot] dispatching → {url}")
    t = threading.Thread(target=_do_visit, args=(url,), daemon=True)
    t.start()


def is_available() -> bool:
    """Check if Playwright + Chromium are installed and launchable."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            b.close()
        return True
    except Exception:
        return False
