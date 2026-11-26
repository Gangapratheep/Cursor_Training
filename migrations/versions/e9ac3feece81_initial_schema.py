"""initial schema

Revision ID: e9ac3feece81
Revises:
Create Date: 2026-11-26 05:10:23.214108

"""

from alembic import op
import sqlalchemy as sa

revision = "e9ac3feece81"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "server",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("ssh_port", sa.Integer(), nullable=False),
        sa.Column("ssh_username", sa.String(length=120), nullable=False),
        sa.Column("auth_type", sa.String(length=20), nullable=False),
        sa.Column("ssh_password", sa.String(length=255), nullable=True),
        sa.Column("ssh_key_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("server")
    op.drop_table("user")
