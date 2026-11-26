"""Custom application errors and Flask error handlers."""

from __future__ import annotations

from flask import Flask, flash, jsonify, redirect, request, url_for


class AppError(Exception):
    """Base application error with a safe user-facing message."""

    status_code = 400

    def __init__(self, message: str = "Request failed", status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404)


def _wants_json() -> bool:
    if request.path.startswith("/api/"):
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json" and (
        request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        app.logger.warning("AppError: %s", exc.message)
        if _wants_json():
            return jsonify({"error": exc.message}), exc.status_code
        flash(exc.message, "error")
        return redirect(url_for("servers.home"))

    @app.errorhandler(404)
    def handle_404(_exc):
        if _wants_json():
            return jsonify({"error": "Not found"}), 404
        return ("Not found", 404)

    @app.errorhandler(500)
    def handle_500(exc):
        app.logger.exception("Unhandled server error: %s", exc)
        if _wants_json():
            return jsonify({"error": "Internal server error"}), 500
        return ("Internal server error", 500)
