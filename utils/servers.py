"""Server form application helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from marshmallow import ValidationError

from models import Server
from schemas.server import ServerFormSchema


def safe_key_path(raw: str) -> Optional[str]:
    path = (raw or "").strip()
    if not path:
        return None
    if ".." in Path(path).parts or re.search(r"[;\|&`$]", path):
        raise ValueError("Invalid key path.")
    return path


def apply_server_form(server: Server, form_data: dict[str, Any], *, is_create: bool) -> Optional[str]:
    """
    Validate and apply form fields onto server.
    Returns a user-facing error message or None on success.
    Never echoes stored secrets into the form model beyond storage.
    """
    raw = {
        "display_name": (form_data.get("display_name") or "").strip(),
        "hostname": (form_data.get("hostname") or "").strip(),
        "auth_type": (form_data.get("auth_type") or "password").strip(),
        "ssh_username": (form_data.get("ssh_username") or "").strip(),
        "ssh_password": form_data.get("ssh_password") or "",
        "ssh_key_path": form_data.get("ssh_key_path") or "",
    }
    try:
        raw["ssh_port"] = int(form_data.get("ssh_port") or 22)
    except (TypeError, ValueError):
        return "SSH port must be a number."

    schema = ServerFormSchema()
    try:
        data = schema.load(raw)
    except ValidationError as exc:
        messages = []
        for value in exc.messages.values():
            if isinstance(value, list):
                messages.extend(str(m) for m in value)
            else:
                messages.append(str(value))
        return messages[0] if messages else "Invalid form data."

    try:
        key_path = safe_key_path(data.get("ssh_key_path") or "")
    except ValueError as exc:
        return str(exc)

    auth_type = data["auth_type"]
    if auth_type == "key" and not key_path and (is_create or not server.ssh_key_path):
        return "SSH key path is required for key auth."

    server.display_name = data["display_name"]
    server.hostname = data["hostname"]
    server.ssh_port = data["ssh_port"]
    server.auth_type = auth_type

    if auth_type == "local":
        server.ssh_username = data["ssh_username"] or "local"
        server.ssh_password = None
        server.ssh_key_path = None
    elif auth_type == "key":
        server.ssh_username = data["ssh_username"]
        if key_path:
            server.ssh_key_path = key_path
        pwd = data.get("ssh_password") or ""
        if pwd:
            server.ssh_password = pwd
    else:
        server.ssh_username = data["ssh_username"]
        server.ssh_key_path = None
        pwd = data.get("ssh_password") or ""
        if is_create:
            server.ssh_password = pwd
        elif pwd:
            server.ssh_password = pwd

    return None
