"""Add payment proof fields to tickets

Revision ID: 007
Revises: 006
Create Date: 2026-01-01 00:06:00
"""
import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tickets" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("tickets")}
    if "payment_proof_filename" not in columns:
        op.add_column("tickets", sa.Column("payment_proof_filename", sa.String(255), nullable=True))
    if "payment_proof_uploaded_at" not in columns:
        op.add_column("tickets", sa.Column("payment_proof_uploaded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "payment_proof_uploaded_at")
    op.drop_column("tickets", "payment_proof_filename")
