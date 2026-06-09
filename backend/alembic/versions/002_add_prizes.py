"""Add prizes table

Revision ID: 002
Revises: 001
Create Date: 2026-01-01 00:01:00
"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "prizes" not in inspector.get_table_names():
        op.create_table(
            "prizes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "raffle_id",
                sa.Integer(),
                sa.ForeignKey("raffles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("image_filename", sa.String(255), nullable=True),
            sa.Column("order", sa.Integer(), server_default="0", nullable=False),
        )
        op.create_index("ix_prizes_id", "prizes", ["id"])
        op.create_index("ix_prizes_raffle_id", "prizes", ["raffle_id"])


def downgrade() -> None:
    op.drop_index("ix_prizes_raffle_id", table_name="prizes")
    op.drop_index("ix_prizes_id", table_name="prizes")
    op.drop_table("prizes")
