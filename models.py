from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(120), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    ssh_port = db.Column(db.Integer, nullable=False, default=22)
    ssh_username = db.Column(db.String(120), nullable=False, default="")
    # local | password | key — SSH password is sensitive; never render in HTML value=
    auth_type = db.Column(db.String(20), nullable=False, default="password")
    ssh_password = db.Column(db.String(255), nullable=True)
    ssh_key_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_local(self) -> bool:
        if self.auth_type == "local":
            return True
        host = (self.hostname or "").strip().lower()
        return host in {"localhost", "127.0.0.1", "::1"}
