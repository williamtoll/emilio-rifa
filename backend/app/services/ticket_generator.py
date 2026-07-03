from sqlalchemy.orm import Session

from app.models import Raffle, Ticket


def normalize_ticket_number(value: str | int) -> str:
    num = int(str(value).strip())
    if num < 1 or num > 9999:
        raise ValueError("El número debe estar entre 1 y 9999")
    return f"{num:04d}"


def generate_ticket_number(db: Session, raffle_id: int) -> str:
    last = (
        db.query(Ticket.ticket_number)
        .filter(Ticket.raffle_id == raffle_id)
        .order_by(Ticket.id.desc())
        .all()
    )
    max_num = 0
    for (ticket_number,) in last:
        try:
            max_num = max(max_num, int(ticket_number))
        except ValueError:
            continue
    return f"{max_num + 1:04d}"


def get_effective_max_tickets(raffle: Raffle, taken: list[str]) -> int:
    if raffle.max_tickets:
        return raffle.max_tickets
    max_taken = max((int(n) for n in taken), default=0)
    return max(100, max_taken + 20)


def is_ticket_number_available(db: Session, raffle_id: int, ticket_number: str) -> bool:
    exists = (
        db.query(Ticket.id)
        .filter(Ticket.raffle_id == raffle_id, Ticket.ticket_number == ticket_number)
        .first()
    )
    return exists is None
