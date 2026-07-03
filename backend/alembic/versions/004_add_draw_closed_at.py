"""Add draw_closed_at to raffles

Revision ID: 004
Revises: 003
Create Date: 2026-01-01 00:03:00
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "raffles" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("raffles")}
    if "draw_closed_at" not in columns:
        op.add_column("raffles", sa.Column("draw_closed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("raffles", "draw_closed_at")
