"""Server inventory HTML routes."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from extensions import db
from models import Server
from utils.auth import login_required
from utils.servers import apply_server_form

servers_bp = Blueprint("servers", __name__)


@servers_bp.route("/")
@login_required
def home():
    servers = Server.query.order_by(Server.display_name).all()
    return render_template("home.html", servers=servers)


@servers_bp.route("/servers/new", methods=["GET", "POST"])
@login_required
def server_new():
    if request.method == "POST":
        server = Server()
        err = apply_server_form(server, request.form, is_create=True)
        if err:
            flash(err, "error")
            return render_template("server_form.html", server=None, title="Add server")
        db.session.add(server)
        db.session.commit()
        current_app.logger.info("Server created: %s", server.display_name)
        flash(f"Server “{server.display_name}” added.", "ok")
        return redirect(url_for("servers.home"))
    return render_template("server_form.html", server=None, title="Add server")


@servers_bp.route("/servers/<int:server_id>/edit", methods=["GET", "POST"])
@login_required
def server_edit(server_id: int):
    server = db.session.get(Server, server_id)
    if server is None:
        return ("Not found", 404)
    if request.method == "POST":
        err = apply_server_form(server, request.form, is_create=False)
        if err:
            flash(err, "error")
            return render_template(
                "server_form.html", server=server, title="Edit server"
            )
        db.session.commit()
        current_app.logger.info("Server updated: %s", server.display_name)
        flash(f"Server “{server.display_name}” updated.", "ok")
        return redirect(url_for("servers.home"))
    return render_template("server_form.html", server=server, title="Edit server")


@servers_bp.route("/servers/<int:server_id>/delete", methods=["POST"])
@login_required
def server_delete(server_id: int):
    server = db.session.get(Server, server_id)
    if server is None:
        return ("Not found", 404)
    name = server.display_name
    db.session.delete(server)
    db.session.commit()
    current_app.logger.info("Server deleted: %s", name)
    flash(f"Server “{name}” removed.", "ok")
    return redirect(url_for("servers.home"))


@servers_bp.route("/servers/<int:server_id>")
@login_required
def server_detail(server_id: int):
    server = db.session.get(Server, server_id)
    if server is None:
        return ("Not found", 404)
    return render_template("server_detail.html", server=server)
