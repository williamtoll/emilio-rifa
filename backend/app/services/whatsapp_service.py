from urllib.parse import quote

from app.models import Ticket
from app.services.ticket_message import build_ticket_message


def normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("52") and len(digits) == 12:
        return digits
    if len(digits) == 10:
        return f"52{digits}"
    return digits


def build_whatsapp_url(ticket: Ticket, custom_message: str | None = None) -> tuple[str, str]:
    if not ticket.buyer_phone:
        raise ValueError("El ticket no tiene teléfono registrado")

    message = build_ticket_message(ticket, custom_message)
    phone = normalize_phone(ticket.buyer_phone)
    url = f"https://wa.me/{phone}?text={quote(message)}"
    return url, message
