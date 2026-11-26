"""Flask configuration objects (development / testing / production-shaped)."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "demo-dev-secret")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'instance' / 'monitoring.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    # Default localhost for local demo; override with BIND_HOST=0.0.0.0 in containers/k8s
    BIND_HOST = os.environ.get("BIND_HOST", "127.0.0.1")
    BIND_PORT = int(os.environ.get("BIND_PORT", "5000"))



class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False


WEAK_SECRET_KEYS = frozenset(
    {
        "",
        "demo-dev-secret",
        "change-me-for-local-demo",
        "change-me-in-cluster",
        "test-secret",
    }
)
WEAK_ADMIN_PASSWORDS = frozenset(
    {
        "",
        "admin123",
        "change-me-admin-password",
        "test-pass-123",
    }
)


def assert_secure_production_config(config: dict) -> None:
    """Fail closed if production still uses demo placeholder secrets."""
    secret = str(config.get("SECRET_KEY") or "")
    admin_pw = str(config.get("ADMIN_PASSWORD") or "")
    if secret in WEAK_SECRET_KEYS:
        raise RuntimeError(
            "FLASK_SECRET_KEY must be set to a strong non-default value in production."
        )
    if admin_pw in WEAK_ADMIN_PASSWORDS:
        raise RuntimeError(
            "ADMIN_PASSWORD must be set to a strong non-default value in production."
        )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
