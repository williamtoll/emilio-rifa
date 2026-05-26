import secrets
import string
import uuid

from sqlalchemy import inspect, text

from app.database import engine

_ALPHABET = string.ascii_letters + string.digits


def _random_short_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(8))


def run_migrations() -> None:
    inspector = inspect(engine)
    if "tickets" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("tickets")}
    with engine.begin() as conn:
        if "public_id" not in columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN public_id VARCHAR(36)"))
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tickets_public_id ON tickets (public_id)")
            )

        if "short_code" not in columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN short_code VARCHAR(12)"))
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tickets_short_code ON tickets (short_code)")
            )

        rows = conn.execute(text("SELECT id FROM tickets WHERE public_id IS NULL")).fetchall()
        for (ticket_id,) in rows:
            conn.execute(
                text("UPDATE tickets SET public_id = :public_id WHERE id = :id"),
                {"public_id": str(uuid.uuid4()), "id": ticket_id},
            )

        rows = conn.execute(text("SELECT id FROM tickets WHERE short_code IS NULL")).fetchall()
        for (ticket_id,) in rows:
            while True:
                code = _random_short_code()
                exists = conn.execute(
                    text("SELECT 1 FROM tickets WHERE short_code = :code"),
                    {"code": code},
                ).first()
                if not exists:
                    conn.execute(
                        text("UPDATE tickets SET short_code = :code WHERE id = :id"),
                        {"code": code, "id": ticket_id},
                    )
                    break
