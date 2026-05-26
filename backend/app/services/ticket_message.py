from app.models import Ticket
from app.utils.currency import format_guaranies


def build_ticket_message(ticket: Ticket, custom_message: str | None = None) -> str:
    raffle = ticket.raffle
    price = float(raffle.ticket_price) if raffle.ticket_price else 0
    paid_status = "PAGADO" if ticket.is_paid else "PENDIENTE DE PAGO"

    base = f"""🎟️ *TICKET DE SORTEO*

*Sorteo:* {raffle.name}
*Número de ticket:* {ticket.ticket_number}
*Participante:* {ticket.buyer_name}
*Precio:* {format_guaranies(price)}
*Estado:* {paid_status}

¡Gracias por participar!"""

    if custom_message:
        return f"{base}\n\n{custom_message}"
    return base
