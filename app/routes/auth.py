from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
import sqlite3, hashlib, uuid

auth_bp = Blueprint("auth", __name__)

def get_db():
    return sqlite3.connect(current_app.config["DATABASE_PATH"])

# ── Login ──────────────────────────────────────────────────────────────────
@auth_bp.route("/", methods=["GET"])
def index():
    if "uuid" in session:
        return redirect(url_for("home.dashboard", player_uuid=session["uuid"]))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "uuid" in session:
        return redirect(url_for("home.dashboard", player_uuid=session["uuid"]))

    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        pw_hash  = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        row  = conn.execute(
            "SELECT id, uuid, username FROM users WHERE email=? AND password=?",
            (email, pw_hash)
        ).fetchone()
        conn.close()

        if row:
            session.permanent = True
            session["user_id"]  = row[0]
            session["uuid"]     = row[1]
            session["username"] = row[2]
            return redirect(url_for("home.dashboard", player_uuid=row[1]))
        error = "INVALID CREDENTIALS. TRY AGAIN."

    return render_template("auth/login.html", error=error)

# ── Register ───────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "uuid" in session:
        return redirect(url_for("home.dashboard", player_uuid=session["uuid"]))

    error   = None
    success = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        pw_hash  = hashlib.sha256(password.encode()).hexdigest()

        if not username or not email or not password:
            error = "ALL FIELDS REQUIRED."
        elif len(username) < 3:
            error = "USERNAME MIN 3 CHARS."
        else:
            conn  = get_db()
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            if count >= current_app.config["MAX_USERS"]:
                error = "SERVER FULL. MAX 10 PLAYERS REACHED."
                conn.close()
            else:
                player_uuid = str(uuid.uuid4())
                try:
                    conn.execute(
                        "INSERT INTO users (uuid, username, email, password) VALUES (?,?,?,?)",
                        (player_uuid, username, email, pw_hash)
                    )
                    uid = conn.execute("SELECT id FROM users WHERE uuid=?", (player_uuid,)).fetchone()[0]
                    for lvl in [1, 2, 99]:
                        conn.execute(
                            "INSERT INTO level_progress (user_id, level, solved) VALUES (?,?,0)",
                            (uid, lvl)
                        )
                    conn.commit()
                    success = "PLAYER REGISTERED! PROCEED TO LOGIN."
                except sqlite3.IntegrityError:
                    error = "USERNAME OR EMAIL ALREADY TAKEN."
                finally:
                    conn.close()

    return render_template("auth/register.html", error=error, success=success)

# ── Logout ─────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
