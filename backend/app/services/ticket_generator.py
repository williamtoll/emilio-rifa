from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Ticket


def generate_ticket_number(db: Session, raffle_id: int) -> str:
    last = (
        db.query(func.max(Ticket.ticket_number))
        .filter(Ticket.raffle_id == raffle_id)
        .scalar()
    )
    if last is None:
        return "0001"
    try:
        next_num = int(last) + 1
    except ValueError:
        count = db.query(Ticket).filter(Ticket.raffle_id == raffle_id).count()
        next_num = count + 1
    return f"{next_num:04d}"
