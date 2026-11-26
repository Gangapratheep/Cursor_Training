"""Marshmallow schemas for Server — never expose SSH secrets."""

from __future__ import annotations

from marshmallow import Schema, ValidationError, fields, validates, validates_schema


class ServerPublicSchema(Schema):
    """Safe server fields for JSON (no password / key material)."""

    id = fields.Int(dump_only=True)
    display_name = fields.Str(required=True)
    hostname = fields.Str(required=True)
    ssh_port = fields.Int(load_default=22)
    auth_type = fields.Str(load_default="password")
    ssh_username = fields.Str(load_default="")


class ServerFormSchema(Schema):
    """Validate add/edit form payloads (HTML forms)."""

    display_name = fields.Str(required=True)
    hostname = fields.Str(required=True)
    ssh_port = fields.Int(load_default=22)
    auth_type = fields.Str(load_default="password")
    ssh_username = fields.Str(load_default="")
    ssh_password = fields.Str(load_default="")
    ssh_key_path = fields.Str(load_default="")

    @validates("display_name")
    def validate_display_name(self, value: str, **_kwargs) -> None:
        if not (value or "").strip():
            raise ValidationError("Display name is required.")

    @validates("hostname")
    def validate_hostname(self, value: str, **_kwargs) -> None:
        if not (value or "").strip():
            raise ValidationError("Hostname is required.")

    @validates("ssh_port")
    def validate_port(self, value: int, **_kwargs) -> None:
        if value < 1 or value > 65535:
            raise ValidationError("SSH port must be between 1 and 65535.")

    @validates("auth_type")
    def validate_auth_type(self, value: str, **_kwargs) -> None:
        if value not in {"local", "password", "key"}:
            raise ValidationError("Invalid authentication type.")

    @validates_schema
    def validate_remote_fields(self, data, **_kwargs) -> None:
        auth_type = data.get("auth_type") or "password"
        if auth_type != "local" and not (data.get("ssh_username") or "").strip():
            raise ValidationError(
                {"ssh_username": ["SSH username is required for remote servers."]}
            )
