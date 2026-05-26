import uuid

from sqlalchemy import inspect, text

from app.database import engine


def ensure_public_id_column() -> None:
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

        rows = conn.execute(text("SELECT id FROM tickets WHERE public_id IS NULL")).fetchall()
        for (ticket_id,) in rows:
            conn.execute(
                text("UPDATE tickets SET public_id = :public_id WHERE id = :id"),
                {"public_id": str(uuid.uuid4()), "id": ticket_id},
            )
