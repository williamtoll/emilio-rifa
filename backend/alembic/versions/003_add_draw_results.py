"""Add draw_results table

Revision ID: 003
Revises: 002
Create Date: 2026-01-01 00:02:00
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "draw_results" not in inspector.get_table_names():
        op.create_table(
            "draw_results",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "raffle_id",
                sa.Integer(),
                sa.ForeignKey("raffles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "prize_id",
                sa.Integer(),
                sa.ForeignKey("prizes.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "ticket_id",
                sa.Integer(),
                sa.ForeignKey("tickets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("drawn_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("raffle_id", "prize_id", name="uq_draw_raffle_prize"),
        )
        op.create_index("ix_draw_results_id", "draw_results", ["id"])
        op.create_index("ix_draw_results_raffle_id", "draw_results", ["raffle_id"])


def downgrade() -> None:
    op.drop_index("ix_draw_results_raffle_id", table_name="draw_results")
    op.drop_index("ix_draw_results_id", table_name="draw_results")
    op.drop_table("draw_results")
