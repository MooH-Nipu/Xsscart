from flask import Flask
from config import Config
import sqlite3, os

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    _init_db(app.config["DATABASE_PATH"])

    from app.routes.auth    import auth_bp
    from app.routes.home    import home_bp
    from app.routes.levels  import levels_bp
    from app.routes.webhook import webhook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(levels_bp)
    app.register_blueprint(webhook_bp)

    return app


def _init_db(db_path: str):
    """Create DB directory, run schema, then migrate any missing columns."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    schema_path = os.path.join(os.path.dirname(__file__), "../database/schema.sql")
    conn = sqlite3.connect(db_path)

    # Create tables that don't exist yet
    with open(schema_path) as f:
        conn.executescript(f.read())

    # ── Auto-migrate: add missing columns to level2_payloads ────────────────
    existing = {row[1] for row in conn.execute("PRAGMA table_info(level2_payloads)")}

    if "reviewer_name" not in existing:
        conn.execute("ALTER TABLE level2_payloads ADD COLUMN reviewer_name TEXT DEFAULT 'Anonymous'")

    if "product_rating" not in existing:
        conn.execute("ALTER TABLE level2_payloads ADD COLUMN product_rating TEXT DEFAULT '5'")

    conn.commit()
    conn.close()
