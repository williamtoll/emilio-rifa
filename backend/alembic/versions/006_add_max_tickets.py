"""Add max_tickets to raffles

Revision ID: 006
Revises: 005
Create Date: 2026-01-01 00:05:00
"""
import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "raffles" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("raffles")}
    if "max_tickets" not in columns:
        op.add_column("raffles", sa.Column("max_tickets", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("raffles", "max_tickets")
