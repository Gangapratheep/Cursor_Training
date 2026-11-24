from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import User, db

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ADMIN_USERNAME = "admin"


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "demo-dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{BASE_DIR / 'instance' / 'monitoring.db'}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Session cookie: HttpOnly by default in Flask; harden for demo
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        # Ensure instance dir exists for default path
        (BASE_DIR / "instance").mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _ensure_admin(app)

    register_routes(app)
    return app


def _ensure_admin(app: Flask) -> None:
    if User.query.filter_by(username=ADMIN_USERNAME).first():
        return
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    if app.config.get("ADMIN_PASSWORD"):
        password = app.config["ADMIN_PASSWORD"]
    user = User(username=ADMIN_USERNAME)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def register_routes(app: Flask) -> None:
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("home"))

        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                nxt = request.args.get("next") or url_for("home")
                if not nxt.startswith("/"):
                    nxt = url_for("home")
                return redirect(nxt)
            # Do not echo password or username details beyond generic message
            flash("Invalid username or password.", "error")

        return render_template("login.html")

    @app.route("/logout", methods=["POST", "GET"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def home():
        return render_template("home.html")


app = create_app()

if __name__ == "__main__":
    # Local demo only — do not bind 0.0.0.0
    app.run(host="127.0.0.1", port=5000, debug=True)
