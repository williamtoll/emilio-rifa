"""Add image_filename to raffles

Revision ID: 005
Revises: 004
Create Date: 2026-01-01 00:04:00
"""
import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "raffles" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("raffles")}
    if "image_filename" not in columns:
        op.add_column("raffles", sa.Column("image_filename", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("raffles", "image_filename")
