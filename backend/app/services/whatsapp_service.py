from urllib.parse import quote

from app.models import Ticket
from app.services.ticket_message import build_ticket_message
from app.utils.phone import to_whatsapp_phone


def build_whatsapp_url(ticket: Ticket, custom_message: str | None = None) -> tuple[str, str]:
    if not ticket.buyer_phone:
        raise ValueError("El ticket no tiene teléfono registrado")

    message = build_ticket_message(ticket, custom_message)
    phone = to_whatsapp_phone(ticket.buyer_phone)
    url = f"https://wa.me/{phone}?text={quote(message)}"
    return url, message
