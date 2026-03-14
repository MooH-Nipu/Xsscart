from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, abort, current_app)
import sqlite3, re

levels_bp = Blueprint("levels", __name__)

# ── helpers ────────────────────────────────────────────────────────────────
def get_db():
    return sqlite3.connect(current_app.config["DATABASE_PATH"])

def require_login(player_uuid):
    return "uuid" in session and session["uuid"] == player_uuid

def get_user(player_uuid):
    conn = get_db()
    row  = conn.execute("SELECT id FROM users WHERE uuid=?", (player_uuid,)).fetchone()
    conn.close()
    return row

def mark_solved(user_id, level):
    conn = get_db()
    conn.execute(
        "UPDATE level_progress SET solved=1, solved_at=CURRENT_TIMESTAMP "
        "WHERE user_id=? AND level=?", (user_id, level))
    conn.commit()
    conn.close()

def is_solved(user_id, level):
    conn = get_db()
    row  = conn.execute(
        "SELECT solved FROM level_progress WHERE user_id=? AND level=?",
        (user_id, level)).fetchone()
    conn.close()
    return bool(row and row[0])

def get_stored_review(user_id):
    conn = get_db()
    row  = conn.execute(
        "SELECT payload, reviewer_name, product_rating FROM level2_payloads WHERE user_id=?",
        (user_id,)).fetchone()
    conn.close()
    return row  # (payload, reviewer_name, rating) or None

def _dispatch_bot(player_uuid):
    from app.bot import dispatch
    base   = current_app.config["APP_BASE_URL"].rstrip("/")
    target = f"{base}/{player_uuid}/home/lvl2/admin"
    dispatch(target)


# ── Level 1 ────────────────────────────────────────────────────────────────
# Block angle brackets and a small set of obvious tag / handler keywords (as whole words)
LEVEL1_BLOCKED = re.compile(
    r"[<>]"
    r"|\bscript\b"
    r"|\bimg\b"
    r"|\bonerror\b"
    r"|\bonload\b"
    r"|\bonclick\b"
    r"|\biframe\b"
    r"|\bsvg\b"
    r"|\bsrcdoc\b",
    re.IGNORECASE,
)

@levels_bp.route("/<player_uuid>/home/lvl1", methods=["GET", "POST"])
def level1(player_uuid):
    if not require_login(player_uuid):
        return redirect(url_for("auth.login"))
    user = get_user(player_uuid)
    if not user:
        abort(404)

    user_id        = user[0]
    already_solved = is_solved(user_id, 1)
    flag = current_app.config["FLAG_PART1"] if already_solved else None
    payload = ""
    error = success = None

    # Always allow experimenting with payloads; solving is based on payload pattern.
    if request.method == "POST":
        payload = request.form.get("payload", "")
        if LEVEL1_BLOCKED.search(payload):
            error = "⛔ PAYLOAD BLOCKED! Forbidden: <, >, 'script', 'img'."
        elif not payload.strip():
            error = "⛔ EMPTY PAYLOAD."
        else:
            # Consider it solved when a javascript: URI is supplied (XSS-style).
            if payload.lower().startswith("javascript:"):
                # First time: mark solved and reveal flag
                if not already_solved:
                    mark_solved(user_id, 1)
                    already_solved = True
                    flag = current_app.config["FLAG_PART1"]
                    success = "✅ SPELL ACCEPTED! THE ORACLE REVEALS YOUR FLAG."
                else:
                    # Subsequent successful payloads still get a toast-style success message
                    success = "✨ SPELL ACCEPTED AGAIN! YOUR MAGIC STILL WORKS."

    return render_template("levels/level1.html",
        player_uuid=player_uuid, payload=payload, flag=flag,
        error=error, success=success, already_solved=already_solved)


# ── Level 2 ────────────────────────────────────────────────────────────────

@levels_bp.route("/<player_uuid>/home/lvl2", methods=["GET", "POST"])
def level2(player_uuid):
    if not require_login(player_uuid):
        return redirect(url_for("auth.login"))
    user = get_user(player_uuid)
    if not user:
        abort(404)

    user_id        = user[0]
    already_solved = is_solved(user_id, 2)
    flag           = current_app.config["FLAG_PART2"] if already_solved else None
    error = success = None
    bot_dispatched = False

    stored_review = get_stored_review(user_id)

    # Auto-dispatch on GET if review exists
    if request.method == "GET" and stored_review and not already_solved:
        _dispatch_bot(player_uuid)
        bot_dispatched = True

    if request.method == "POST" and not already_solved:
        action = request.form.get("action")

        # ── A: Post review (the XSS payload disguised as a product review) ──
        if action == "post_review":
            reviewer_name = request.form.get("reviewer_name", "Anonymous").strip() or "Anonymous"
            rating        = request.form.get("rating", "5").strip()
            review_body   = request.form.get("review_body", "").strip()

            if not review_body:
                error = "⛔ Review body cannot be empty."
            else:
                conn = get_db()
                conn.execute(
                    "INSERT INTO level2_payloads (user_id, payload, reviewer_name, product_rating) "
                    "VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET "
                    "payload=excluded.payload, reviewer_name=excluded.reviewer_name, "
                    "product_rating=excluded.product_rating, created_at=CURRENT_TIMESTAMP",
                    (user_id, review_body, reviewer_name, rating))
                conn.commit()
                conn.close()
                stored_review = (review_body, reviewer_name, rating)

                # Dispatch bot to see the review
                _dispatch_bot(player_uuid)
                bot_dispatched = True
                success = "📝 Review posted! Admin moderator dispatched to review it..."

        # ── B: Re-dispatch bot ───────────────────────────────────────────────
        elif action == "dispatch":
            if not stored_review:
                error = "⛔ Post a review first."
            else:
                _dispatch_bot(player_uuid)
                bot_dispatched = True
                success = "🤖 Admin bot re-dispatched! Check your webhook..."

        # ── C: Submit stolen cookie as proof ────────────────────────────────
        elif action == "claim":
            submitted = request.form.get("stolen_cookie", "").strip()
            expected  = current_app.config["ADMIN_COOKIE"]
            if not submitted:
                error = "⛔ Paste the cookie value from your webhook."
            elif submitted == expected:
                mark_solved(user_id, 2)
                already_solved = True
                flag    = current_app.config["FLAG_PART2"]
                success = "✅ COOKIE VERIFIED! LEVEL CLEARED!"
            else:
                error = "⛔ WRONG COOKIE VALUE. Check your webhook again."

    return render_template("levels/level2.html",
        player_uuid    = player_uuid,
        stored_review  = stored_review,
        flag           = flag,
        error          = error,
        success        = success,
        already_solved = already_solved,
        bot_dispatched = bot_dispatched,
    )


# ── Admin review page (what the bot visits — intentionally vulnerable) ──────
@levels_bp.route("/<player_uuid>/home/lvl2/admin")
def level2_admin(player_uuid):
    """
    Simulates the admin's review moderation panel.
    The stored review body is rendered UNESCAPED — this is the intended vuln.
    """
    user = get_user(player_uuid)
    if not user:
        abort(404)

    conn = get_db()
    row  = conn.execute(
        "SELECT payload, reviewer_name, product_rating, created_at "
        "FROM level2_payloads WHERE user_id=?", (user[0],)).fetchone()
    conn.close()

    if not row:
        return "<h2>No pending reviews.</h2>"

    from markupsafe import Markup
    return render_template("levels/level2_admin.html",
        review_body   = Markup(row[0]),   # ← intentionally unescaped
        reviewer_name = row[1],
        rating        = row[2],
        created_at    = row[3],
        player_uuid   = player_uuid)


# ── Bonus Level ────────────────────────────────────────────────────────────
@levels_bp.route("/<player_uuid>/home/bonus", methods=["GET", "POST"])
def bonus(player_uuid):
    if not require_login(player_uuid):
        return redirect(url_for("auth.login"))
    user = get_user(player_uuid)
    if not user:
        abort(404)

    user_id        = user[0]
    already_solved = is_solved(user_id, 99)
    flag = "ITDIV{y0u_found_th3_h1dd3n_funct10n}" if already_solved else None
    error = success = None

    if request.method == "POST" and not already_solved:
        payload = request.form.get("payload", "").strip()
        # Accept anything that calls __xsscart_unlock__
        if "__xsscart_unlock__" in payload:
            mark_solved(user_id, 99)
            already_solved = True
            flag    = "ITDIV{y0u_found_th3_h1dd3n_funct10n}"
            success = "✅ HIDDEN FUNCTION FOUND & CALLED! BONUS CLEARED!"
        elif payload:
            error = "⛔ Payload doesn't seem to call the right function..."

    return render_template("levels/bonus.html",
        player_uuid    = player_uuid,
        already_solved = already_solved,
        flag           = flag,
        error          = error,
        success        = success,
    )
