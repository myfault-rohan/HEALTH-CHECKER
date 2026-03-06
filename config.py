import os
from pathlib import Path


class Config:
    """Application settings loaded into Flask."""

    BASE_DIR = Path(__file__).resolve().parent
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "health_checker.db"),
    )
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "local-dev-secret-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

