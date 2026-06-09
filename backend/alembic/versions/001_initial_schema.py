"""Initial schema: raffles and tickets

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00
"""
import secrets
import string
import uuid

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

_ALPHABET = string.ascii_letters + string.digits


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    # ── raffles ──────────────────────────────────────────────────────────────
    if "raffles" not in existing:
        op.create_table(
            "raffles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("ticket_price", sa.Numeric(10, 2), server_default="0", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_raffles_id", "raffles", ["id"])

    # ── tickets ───────────────────────────────────────────────────────────────
    if "tickets" not in existing:
        op.create_table(
            "tickets",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("public_id", sa.String(36), nullable=True),
            sa.Column("short_code", sa.String(12), nullable=True),
            sa.Column(
                "raffle_id",
                sa.Integer(),
                sa.ForeignKey("raffles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("ticket_number", sa.String(20), nullable=False),
            sa.Column("buyer_name", sa.String(200), nullable=False),
            sa.Column("buyer_phone", sa.String(30), nullable=True),
            sa.Column("buyer_email", sa.String(200), nullable=True),
            sa.Column("is_paid", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("raffle_id", "ticket_number", name="uq_raffle_ticket_number"),
        )
        op.create_index("ix_tickets_id", "tickets", ["id"])
        op.create_index("ix_tickets_public_id", "tickets", ["public_id"], unique=True)
        op.create_index("ix_tickets_short_code", "tickets", ["short_code"], unique=True)
    else:
        # ── Existing DB: add columns that may be missing (legacy support) ──
        ticket_cols = {c["name"] for c in inspector.get_columns("tickets")}
        existing_indexes = {i["name"] for i in inspector.get_indexes("tickets")}

        if "public_id" not in ticket_cols:
            op.add_column("tickets", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_tickets_public_id" not in existing_indexes:
            op.create_index("ix_tickets_public_id", "tickets", ["public_id"], unique=True)

        if "short_code" not in ticket_cols:
            op.add_column("tickets", sa.Column("short_code", sa.String(12), nullable=True))
        if "ix_tickets_short_code" not in existing_indexes:
            op.create_index("ix_tickets_short_code", "tickets", ["short_code"], unique=True)

        # ── Backfill public_id ────────────────────────────────────────────────
        rows = bind.execute(
            sa.text("SELECT id FROM tickets WHERE public_id IS NULL")
        ).fetchall()
        for (ticket_id,) in rows:
            bind.execute(
                sa.text("UPDATE tickets SET public_id = :uid WHERE id = :id"),
                {"uid": str(uuid.uuid4()), "id": ticket_id},
            )

        # ── Backfill short_code ───────────────────────────────────────────────
        rows = bind.execute(
            sa.text("SELECT id FROM tickets WHERE short_code IS NULL")
        ).fetchall()
        for (ticket_id,) in rows:
            while True:
                code = "".join(secrets.choice(_ALPHABET) for _ in range(8))
                exists = bind.execute(
                    sa.text("SELECT 1 FROM tickets WHERE short_code = :code"),
                    {"code": code},
                ).first()
                if not exists:
                    bind.execute(
                        sa.text("UPDATE tickets SET short_code = :code WHERE id = :id"),
                        {"code": code, "id": ticket_id},
                    )
                    break


def downgrade() -> None:
    # Intentionally a no-op: dropping the initial tables would destroy all data.
    pass
