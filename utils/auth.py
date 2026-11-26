"""Session-based auth helpers (DemoMonitor uses HttpOnly session cookies, not JWT)."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import redirect, request, session, url_for

F = TypeVar("F", bound=Callable)


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def is_authenticated() -> bool:
    return bool(session.get("user_id"))
