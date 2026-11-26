"""DemoMonitor application factory and entrypoint."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask

from blueprints.api import api_bp
from blueprints.auth import auth_bp
from blueprints.servers import servers_bp
from config import (
    BASE_DIR,
    DevelopmentConfig,
    assert_secure_production_config,
    config_by_name,
)
from errors import register_error_handlers
from extensions import db, migrate
from models import User

load_dotenv(BASE_DIR / ".env")


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    env_name = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, DevelopmentConfig))

    if test_config:
        app.config.update(test_config)
    elif env_name == "production":
        assert_secure_production_config(app.config)

    _configure_logging(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if str(app.config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("sqlite:///"):
        (BASE_DIR / "instance").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    register_error_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(servers_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        _ensure_admin(app)

    app.logger.info("DemoMonitor app initialized")
    return app


def _configure_logging(app: Flask) -> None:
    if app.logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)


def _ensure_admin(app: Flask) -> None:
    username = app.config.get("ADMIN_USERNAME", "admin")
    if User.query.filter_by(username=username).first():
        return
    password = app.config.get("ADMIN_PASSWORD") or os.environ.get(
        "ADMIN_PASSWORD", "admin123"
    )
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    app.logger.info("Seeded admin user")


app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config.get("BIND_HOST", "127.0.0.1"),
        port=int(app.config.get("BIND_PORT", 5000)),
        debug=bool(app.config.get("DEBUG", True)),
    )
