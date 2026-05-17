import os
from pathlib import Path


class Config:
    """Application settings loaded into Flask."""

    BASE_DIR = Path(__file__).resolve().parent
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "health_checker.db"),
    )
    _is_production = os.getenv("FLASK_ENV", "").strip().lower() == "production"
    _secret_key = os.getenv("FLASK_SECRET_KEY")
    if _is_production and not _secret_key:
        raise RuntimeError(
            "FLASK_SECRET_KEY must be set when FLASK_ENV=production."
        )
    SECRET_KEY = _secret_key or "local-dev-secret-change-me"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
