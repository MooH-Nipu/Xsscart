import os

_BASE = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY    = os.environ.get("SECRET_KEY",    "pixel-ctf-secret-key-change-me")
    # Default: store DB in project folder so it works on both Windows and Linux
    DATABASE_PATH = os.environ.get("DATABASE_PATH",
                        os.path.join(_BASE, "database", "xsscart.db"))
    MAX_USERS     = 10
    FLAG_PART1    = os.environ.get("FLAG_PART1",    "ITDIV{bina_nus")
    FLAG_PART2    = os.environ.get("FLAG_PART2",    "dont_try_to_guess_the_flag_dude_play_the_other_part}")
    ADMIN_COOKIE  = os.environ.get("ADMIN_COOKIE",  "supersecretadmincookie_xsscart")
    APP_BASE_URL  = os.environ.get("APP_BASE_URL",  "http://localhost:5000")
    ADMIN_COOKIE_NAME = os.environ.get("ADMIN_COOKIE_NAME", "admin_session")
    BOT_WAIT_MS   = int(os.environ.get("BOT_WAIT_MS", "5000"))
