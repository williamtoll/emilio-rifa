"""Add reservation_group_id to tickets

Revision ID: 008
Revises: 007
Create Date: 2026-01-01 00:07:00
"""
import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tickets" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("tickets")}
    if "reservation_group_id" not in columns:
        op.add_column("tickets", sa.Column("reservation_group_id", sa.String(36), nullable=True))
        op.create_index("ix_tickets_reservation_group_id", "tickets", ["reservation_group_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_reservation_group_id", table_name="tickets")
    op.drop_column("tickets", "reservation_group_id")
