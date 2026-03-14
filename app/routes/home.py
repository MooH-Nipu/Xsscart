from flask import Blueprint, render_template, session, redirect, url_for, abort, current_app
import sqlite3

home_bp = Blueprint("home", __name__)

def get_db():
    return sqlite3.connect(current_app.config["DATABASE_PATH"])

def require_login(player_uuid):
    if "uuid" not in session or session["uuid"] != player_uuid:
        return False
    return True

@home_bp.route("/<player_uuid>/home")
def dashboard(player_uuid):
    if not require_login(player_uuid):
        return redirect(url_for("auth.login"))

    conn     = get_db()
    user     = conn.execute("SELECT id, username FROM users WHERE uuid=?", (player_uuid,)).fetchone()
    if not user:
        abort(404)

    progress = conn.execute(
        "SELECT level, solved, solved_at FROM level_progress WHERE user_id=? ORDER BY level",
        (user[0],)
    ).fetchall()
    conn.close()

    # Build level map: {level: {solved, solved_at}}
    level_map = {}
    for lvl, solved, solved_at in progress:
        level_map[lvl] = {"solved": bool(solved), "solved_at": solved_at}

    solved_count = sum(1 for v in level_map.values() if v["solved"])

    return render_template("home/dashboard.html",
        username     = user[1],
        player_uuid  = player_uuid,
        level_map    = level_map,
        solved_count = solved_count,
    )
