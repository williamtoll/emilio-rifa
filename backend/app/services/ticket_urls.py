from app.config import settings
from app.models import Ticket


def get_public_ticket_url(ticket: Ticket) -> str:
    return f"{settings.app_base_url.rstrip('/')}/t/{ticket.public_id}"
