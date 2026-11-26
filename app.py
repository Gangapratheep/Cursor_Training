from __future__ import annotations

import os
import re
from functools import wraps
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from metrics import collect_for_server
from models import Server, User, db

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
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
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


def _safe_key_path(raw: str) -> Optional[str]:
    path = (raw or "").strip()
    if not path:
        return None
    # Reject traversal and shell metacharacters (demo hardening)
    if ".." in Path(path).parts or re.search(r"[;\|&`$]", path):
        raise ValueError("Invalid key path.")
    return path


def _apply_server_form(server: Server, *, is_create: bool) -> Optional[str]:
    """Apply form fields onto server. Returns error message or None."""
    display_name = (request.form.get("display_name") or "").strip()
    hostname = (request.form.get("hostname") or "").strip()
    auth_type = (request.form.get("auth_type") or "password").strip()
    ssh_username = (request.form.get("ssh_username") or "").strip()

    if not display_name or not hostname:
        return "Display name and hostname are required."
    if auth_type not in {"local", "password", "key"}:
        return "Invalid authentication type."

    try:
        ssh_port = int(request.form.get("ssh_port") or 22)
    except ValueError:
        return "SSH port must be a number."
    if ssh_port < 1 or ssh_port > 65535:
        return "SSH port must be between 1 and 65535."

    if auth_type != "local" and not ssh_username:
        return "SSH username is required for remote servers."

    try:
        key_path = _safe_key_path(request.form.get("ssh_key_path") or "")
    except ValueError as exc:
        return str(exc)

    if auth_type == "key" and not key_path and (is_create or not server.ssh_key_path):
        return "SSH key path is required for key auth."

    server.display_name = display_name
    server.hostname = hostname
    server.ssh_port = ssh_port
    server.auth_type = auth_type

    if auth_type == "local":
        server.ssh_username = ssh_username or "local"
        server.ssh_password = None
        server.ssh_key_path = None
    elif auth_type == "key":
        server.ssh_username = ssh_username
        if key_path:
            server.ssh_key_path = key_path
        # Blank password field = keep existing (never echo stored secret)
        pwd = request.form.get("ssh_password")
        if pwd:
            server.ssh_password = pwd
    else:
        server.ssh_username = ssh_username
        server.ssh_key_path = None
        pwd = request.form.get("ssh_password")
        if is_create:
            server.ssh_password = pwd or ""
        elif pwd:
            server.ssh_password = pwd

    return None


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
            flash("Invalid username or password.", "error")

        return render_template("login.html")

    @app.route("/logout", methods=["POST", "GET"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def home():
        servers = Server.query.order_by(Server.display_name).all()
        return render_template("home.html", servers=servers)

    @app.route("/servers/new", methods=["GET", "POST"])
    @login_required
    def server_new():
        if request.method == "POST":
            server = Server()
            err = _apply_server_form(server, is_create=True)
            if err:
                flash(err, "error")
                return render_template("server_form.html", server=None, title="Add server")
            db.session.add(server)
            db.session.commit()
            flash(f"Server “{server.display_name}” added.", "ok")
            return redirect(url_for("home"))
        return render_template("server_form.html", server=None, title="Add server")

    @app.route("/servers/<int:server_id>/edit", methods=["GET", "POST"])
    @login_required
    def server_edit(server_id: int):
        server = db.session.get(Server, server_id)
        if server is None:
            return ("Not found", 404)
        if request.method == "POST":
            err = _apply_server_form(server, is_create=False)
            if err:
                flash(err, "error")
                return render_template(
                    "server_form.html", server=server, title="Edit server"
                )
            db.session.commit()
            flash(f"Server “{server.display_name}” updated.", "ok")
            return redirect(url_for("home"))
        return render_template("server_form.html", server=server, title="Edit server")

    @app.route("/servers/<int:server_id>/delete", methods=["POST"])
    @login_required
    def server_delete(server_id: int):
        server = db.session.get(Server, server_id)
        if server is None:
            return ("Not found", 404)
        name = server.display_name
        db.session.delete(server)
        db.session.commit()
        flash(f"Server “{name}” removed.", "ok")
        return redirect(url_for("home"))

    @app.route("/servers/<int:server_id>")
    @login_required
    def server_detail(server_id: int):
        server = db.session.get(Server, server_id)
        if server is None:
            return ("Not found", 404)
        return render_template("server_detail.html", server=server)

    @app.route("/api/servers/<int:server_id>/metrics")
    @login_required
    def api_server_metrics(server_id: int):
        server = db.session.get(Server, server_id)
        if server is None:
            return jsonify({"error": "Not found"}), 404
        payload = collect_for_server(server)
        return jsonify(payload)

    @app.route("/api/servers/metrics")
    @login_required
    def api_servers_metrics_batch():
        servers = Server.query.order_by(Server.display_name).all()
        items = []
        for server in servers:
            metrics = collect_for_server(server)
            items.append(
                {
                    "id": server.id,
                    "display_name": server.display_name,
                    "hostname": server.hostname,
                    "ssh_port": server.ssh_port,
                    "auth_type": server.auth_type,
                    "metrics": metrics,
                }
            )
        return jsonify({"servers": items})


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
