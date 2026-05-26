from urllib.parse import quote

from app.models import Ticket
from app.services.ticket_urls import get_short_ticket_url


def build_whatsapp_share_message(ticket: Ticket, custom_message: str | None = None) -> str:
    raffle = ticket.raffle
    link = get_short_ticket_url(ticket)
    base = (
        f"🎟️ *Tu ticket — {raffle.name}*\n\n"
        f"*Número:* #{ticket.ticket_number}\n\n"
        f"👉 Ver tu ticket:\n{link}"
    )
    if custom_message:
        return f"{base}\n\n{custom_message}"
    return base


def build_whatsapp_url(ticket: Ticket, custom_message: str | None = None) -> tuple[str, str]:
    if not ticket.buyer_phone:
        raise ValueError("El ticket no tiene teléfono registrado")
    if not ticket.is_paid:
        raise ValueError("El ticket debe estar pagado para compartir por WhatsApp")
    if not ticket.short_code:
        raise ValueError("El ticket no tiene enlace corto generado")

    message = build_whatsapp_share_message(ticket, custom_message)
    from app.utils.phone import to_whatsapp_phone

    phone = to_whatsapp_phone(ticket.buyer_phone)
    url = f"https://wa.me/{phone}?text={quote(message)}"
    return url, message
