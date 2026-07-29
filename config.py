import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-before-production",
    )

    GOOGLE_OAUTH_CLIENT_ID = os.environ.get(
        "GOOGLE_OAUTH_CLIENT_ID",
    )

    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get(
        "GOOGLE_OAUTH_CLIENT_SECRET",
    )

    PLACES_PROVIDER = os.environ.get(
        "PLACES_PROVIDER",
        "mock",
    ).strip().lower()

    ASSISTANT_PROVIDER = os.environ.get(
        "ASSISTANT_PROVIDER",
        "fake",
    ).strip().lower()

    OPENAI_API_KEY = os.environ.get(
        "OPENAI_API_KEY",
    )

    ASSISTANT_MODEL = os.environ.get(
        "ASSISTANT_MODEL",
    )

    PLACES_API_KEY = os.environ.get(
        "PLACES_API_KEY",
    )

    MAPS_JAVASCRIPT_API_KEY = os.environ.get(
        "MAPS_JAVASCRIPT_API_KEY",
    )

    GOOGLE_MAP_ID = os.environ.get(
        "GOOGLE_MAP_ID",
    )

    PLACES_REQUEST_TIMEOUT_SECONDS = float(
        os.environ.get(
            "PLACES_REQUEST_TIMEOUT_SECONDS",
            "10",
        )
    )

    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'cityguide.db'}",
    )

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.environ.get("FLASK_ENV") == "production"
    )

    ADMIN_EMAILS = frozenset(
        email.strip().lower()
        for email in os.environ.get(
            "ADMIN_EMAILS",
            "",
        ).split(",")
        if email.strip()
    )
